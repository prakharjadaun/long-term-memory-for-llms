# Long Term Memory For LLMS

This project showcases the approach to incorporate long term memory with llms.

## **Setup**

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
