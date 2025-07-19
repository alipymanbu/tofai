# Helper util to see the exact prompt being fed to each LLM call.
# This is useful for debugging and understanding the prompt structure.

# Example usage:
# python3 -m services.ai.configs.prompt_output_util > output_prompts.txt
# The output will be saved in output_prompts.txt
from services.ai.tasks.generator import Generator

def generate_prompt_templates(framework_id):
  """
  Generate prompt templates based on the given framework_id.

  Args:
    framework_id (str): The ID of the framework to generate prompts for.

  Returns:
    dict: A dictionary containing the generated prompt templates.
  """
  generator = Generator(framework_id)
  result = generator.generate_prompt_templates()
  for step, value in result.items():
    print(f"step: {step}\nprompt: {value}\n")
    print("=====================================\n\n")
  return result

if __name__ == "__main__":
  # Example usage
  framework_id = "brand_awareness_framework"
  generate_prompt_templates(framework_id)