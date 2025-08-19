

from multiprocessing import context
import os
from dotenv import load_dotenv
from agents import (
   Agent,
   Runner,
   function_tool,
   input_guardrail,
   RunContextWrapper,
   model_settings,
   AsyncOpenAI,
   OpenAIChatCompletionsModel,
   TResponseInputItem,
   GuardrailFunctionOutput,
   set_tracing_disabled,
   
   )
from pydantic import BaseModel

load_dotenv()
set_tracing_disabled(True)



gemini_api_key=os.getenv("GEMINI_API_KEY")


external_client=AsyncOpenAI(
    api_key=gemini_api_key,
    )
model=OpenAIChatCompletionsModel(
    openai_client=external_client,
    model="gemini-2.5-flash",
 )

class RegisteredMembers(BaseModel):
    user_id: int
    name: str
    
class NonLibraryQuestionRequest(BaseModel):
    is_non_library: bool
    reasoning: str


@function_tool
def search_books():
    """Search for books in the library."""
    return {"books": ["Book 1", "Book 2", "Book 3"]}

@function_tool
def check_book_availability():
    """Check if a book is available for a user."""
    return {"available": True}


@function_tool
def get_library_timings():
    """Get the library's opening and closing timings."""
    return {"opening_hours": "9 AM - 5 PM"}


@function_tool
def handle_non_library_question():
    """Handle questions that are not related to the library."""
    return {"response": "I'm sorry, I can only assist with library-related inquiries."}

guardrail_agent=Agent(
    name="library question",
    instructions="check if non-library question is about the library",
    output_type=NonLibraryQuestionRequest,
    model=model,
)


@input_guardrail
async def library_guardrail(
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
       result= await Runner.run(guardrail_agent,input,context=ctx.context)

       return GuardrailFunctionOutput(
           output_info=result.output_final_output,
           tripwire_triggered=result.final_output.is_non_library,
       )
def register_member(ctx:RunContextWrapper[RegisteredMembers]) -> bool:
        if ctx.context.name == "faisal" and ctx.context.user_id == 12345:
           return True
        elif ctx.context.name == "john" and ctx.context.user_id == 67890:
           return True
        return False
def dynamic_instruction(ctx: RunContextWrapper[RegisteredMembers], agent: Agent):
   return f" user {ctx.context.name} is a registered member."

library_agent=Agent(
       name="library_agent",
       instructions=dynamic_instruction,
       input_guardrails=[library_guardrail],
       tools=[
           search_books,
        check_book_availability,
        get_library_timings,
        handle_non_library_question,
    ],
        model=model,
  )

user_context=RegisteredMembers(name="faisal", user_id=12345)
result=Runner.run_sync(library_agent,"library hours, search for books", context=user_context)