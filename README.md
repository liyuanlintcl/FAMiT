### Quick Start

#### Environment Setup

```shell
python3 -m venv <name>
source <name>/bin/activate
pip install -r ./requirements.txt  
```

#### Run Pysa 

```shell
pyre analyze --no-verify --save-results-to ./bench/pysa-runs
```

#### Run FAMiT

You should use your own api-key before run FAMiT.

```shell
python3 ./analysis.py
```

#### Run Real-World Project

Download the project locally and modify the corresponding path information in `analysis.py`. Enter the project folder, run the bash below:

```
#!/bin/bash

current_dir=$(pwd)

test_project="xxx"

dir="$current_dir/$test_project"

if [ -d "$dir" ]; then  # 检查是否为目录
    # 进入目录
    cd "$dir"

    echo "{\"source_directories\": [\"$dir\"],\"taint_models_path\": [\"../pysa/stubs/taint/\"],\"search_path\": [\"<folder path of the README.md>/bench/stubs\"]}" > .pyre_configuration

    pyre analyze --no-verify --save-results-to $dir/pysa-runs
fi
```

