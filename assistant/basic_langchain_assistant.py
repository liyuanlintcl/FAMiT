import inspect
import logging
import time
import uuid

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger('FAMiT')


class BasicAssistant:
    def __init__(self, llm_model, prompts, validation_path=None, o1=False, **kwargs):
        self.prompts = None
        llm = ChatOpenAI(
            model=llm_model["model"],
            openai_api_key=llm_model["api_key"],
            openai_api_base=llm_model["api_base"],
        )

        self.o1 = o1
        self.get_prompts(prompts)

        def call_model(state: MessagesState):
            model = self.prompts | llm
            response = model.invoke(state["messages"])
            return {"messages": response}

        workflow = StateGraph(state_schema=MessagesState)

        workflow.add_edge(START, "model")
        workflow.add_node("model", call_model)

        memory = MemorySaver()
        self.app = workflow.compile(checkpointer=memory)

        thread_id = uuid.uuid4()
        self.config = {"configurable": {"thread_id": thread_id}}

        if not o1:
            self.memory = [{"role": "system", "content": self.prompts}]
        else:
            self.memory = [{"role": "user", "content": self.prompts}]

        if validation_path:
            with open(validation_path, 'r', encoding='utf-8') as f:
                self.validation = f.read()
        else:
            self.validation = None

    def get_prompts(self, prompt_paths):
        prompts = ""
        for prompt_path in prompt_paths:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompts += f.read() + '\n\n'
        if not self.o1:
            self.prompts = ChatPromptTemplate.from_messages(
                [
                    ("system", prompts),
                    MessagesPlaceholder(variable_name="messages")
                ]
            )
        else:
            self.prompts = ChatPromptTemplate.from_messages(
                [
                    ("user", prompts),
                    MessagesPlaceholder(variable_name="messages")
                ]
            )

    def clean_messages(self):
        thread_id = uuid.uuid4()
        self.config = {"configurable": {"thread_id": thread_id}}

    def self_validation(self):
        if self.validation:
            return self.send_message(self.validation)

    def vote(self, analysis_func, check_func, iter_num=1, beam_num=3, first_answer=True):
        vote_count = 0
        vote_reason = {}
        for i in range(iter_num):
            if vote_count > iter_num / 2 or vote_count + iter_num - i < iter_num / 2:
                break
            try:
                if first_answer and i == 0:
                    analysis_result, analysis_reason = check_func(self.app.get_state(self.config).values['messages'][-1].content)
                else:
                    analysis_result, analysis_reason = self.beam(analysis_func, check_func, beam_num)
            except Exception as e:
                logger.exception(e)
                analysis_result, analysis_reason = None, None
            if analysis_result is None:
                continue
            vote_count += analysis_result
            vote_reason[analysis_result] = analysis_reason
        analysis_result = vote_count > iter_num / 2
        analysis_reason = vote_reason[analysis_result]
        return analysis_result, analysis_reason

    def beam(self, analysis_func, check_func, beam_num=3):
        analysis = analysis_func()
        beam_state = None
        for i, state in enumerate(self.app.get_state_history(self.config)):
            if i == 1:
                beam_state = state
                break
        beam_reason = {}
        beam_count = 0
        beam_states: dict = {}
        for i in range(beam_num):
            if i != 0:
                analysis = self.send_message(config=beam_state.config)
            analysis_result, analysis_reason = check_func(analysis)
            beam_states[analysis_result] = self.app.get_state(self.config)
            if isinstance(analysis_reason, list):
                beam_count |= analysis_result
                if analysis_result and len(analysis_reason) > len(beam_reason):
                    beam_reason = analysis_reason
            else:
                beam_count += analysis_result
                beam_reason[analysis_result] = analysis_reason
                if beam_count > beam_num / 2 or beam_count + beam_num - i < beam_num / 2 or i == beam_num - 1:
                    beam_count = beam_count > beam_num / 2
                    beam_reason = beam_reason[beam_count]
                    break
        beam_state = beam_states[beam_count]
        self.app.update_state(self.config, beam_state.values)
        return beam_count, beam_reason

    def send_message(self, message=None, config=None):
        if message is not None:
            logger.info("\n" + message)
            message = {"messages": message}

        if config is None:
            config = self.config

        res = None
        while True:
            try:
                for event in self.app.stream(message, config, stream_mode="values"):
                    if "messages" in event:
                        res = event['messages'][-1].content
            except Exception as e:
                time.sleep(10)
            else:
                break
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back
            code = caller_frame.f_code
            caller_function_name = code.co_name
        finally:
            del frame

        logger.info(
            f'\n--------------------------{self.__class__.__name__}.{caller_function_name}--------------------------\n{res}\n--------------------------{self.__class__.__name__}.{caller_function_name}--------------------------')
        return res

    @staticmethod
    def check_result(assistant_origin_result, assistant_answer_again, check_result_function):
        result = check_result_function(assistant_origin_result)
        loop_time = 0
        while result is None:
            result = assistant_answer_again()
            result = check_result_function(result)
            loop_time += 1
            if loop_time > 5:
                raise Exception("loop_time exceeds 5")
        return result
