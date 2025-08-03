from prompts.memory_categories import categories

chat_history_summary_prompt="""You are a summary writer for the provided chat history to you. Summary is to be generated such that later the summary can be retrieved using the vector search.
Through vector search I am providing the llm a extended memory to search on.

You would require to generate a list of memory segments if there are multiple aspects discussed in the chat history else a only one object would also be okay

Generate the summary in the below JSON format.
>>>
{ 
"segments": [{
    "memory": "<memory that has to be added to the vector store>",
    "category": "<category to which the memory segment belongs to. categories are provided below>"
}]
}
<<<

## Guidelines:
- Generate the response in JSON format containing the list of dictionaries having the memory and category key.
- Strictly give the relevant information in the memory key.
""" + f"""Here are the categories from which you need to pick the category from:
{categories}
"""
