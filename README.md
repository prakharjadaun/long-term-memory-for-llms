# Long Term Memory For LLMS

This project showcases the approach to incorporate long term memory with llms.

## **Features**

- Supports both OpenAI and Azure OpenAI for chat and embedding models
- Async provider with support for AsyncOpenAI and AsyncAzureOpenAI
- Pydantic-based configuration validation (env and YAML)
- Loguru logging throughout (info, warning, exception)
- Semantic memory tools (add/update/delete memory via Azure AI Search)
- Chainlit-based UI with streaming and session management
- Structured project layout (prompts, tools, services, handlers)

## **Setup**

<details>

<summary>Click to expand the setup instructions</summary>

I have utilized conda to create and manage the environments.

1. Environment creation

    ```sh
    conda create -n long_term_llm_memory python==3.12 -y
    ```

2. Activate your environment.

    ```sh
    conda activate long_term_llm_memory
    ```

3. Install poetry.

    ```py
    pip install poetry
    ```

   > if pip shows any error for example `Unable to create process using ....` use the below command

   ```py
   python -m pip install --upgrade --force-reinstall pip
   ```

4. Setup the project/package.

    ```sh
    poetry install
    ```

5. Perform the selection of the llm, currently the project supports OPENAI API or Azure OpenAI endpoints and embedding models.

    > llm_config.yaml

6. Run the chainlit app.

   ```sh
   chainlit run app.py -w
   ```

</details>