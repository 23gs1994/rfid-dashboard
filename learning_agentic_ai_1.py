from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import torch

class SimpleAgenticAI:
    def __init__(self, model_name="mistralai/Mistral-7B-Instruct-v0.2"):
        print("Loading model... (this may take a minute)")

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,                         # or load_in_4bit=True for smaller size
            llm_int8_enable_fp32_cpu_offload=True,     # <- This is key!
        )
        # Load model with GPU support if available
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,       # Use half precision (faster and smaller)
            quantization_config=self.bnb_config,  # Use the BitsAndBytesConfig for quantization
            device_map="auto",               # Automatically use available GPU(s)
            trust_remote_code=True           # Just in case the model uses custom code
        )

        # Load generation pipeline to run on GPU
        self.generator = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            # device=0 if torch.cuda.is_available() else -1,  # 0 = GPU, -1 = CPU
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )

        self.memory = ""

    def ask(self, prompt, max_new_tokens=200):
        result = self.generator(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id  # avoid warning
        )
        return result[0]["generated_text"][len(prompt):].strip()

    def plan_tasks(self, goal):
        prompt = f"""You are an AI agent. Break the following goal into 3-5 numbered steps.
Goal: {goal}
Plan:"""
        return self.ask(prompt)

    def execute_task(self, task):
        prompt = f"""You are an expert agent. Use the following memory to help you perform the task.
Memory: {self.memory}
Task: {task}
Answer:"""
        return self.ask(prompt)

    def reflect(self, result):
        prompt = f"""You are a critical thinking AI. Reflect on this output and summarize whether it is complete or needs improvement.
Output: {result}
Reflection:"""
        return self.ask(prompt)

    def run(self, goal):
        print(f"🎯 Goal: {goal}\n")
        plan = self.plan_tasks(goal)
        print("📝 Plan:")
        print(plan)

        steps = [line for line in plan.split('\n') if line.strip().startswith(tuple("123456789"))]

        for idx, step in enumerate(steps, 1):

            print(f"\n🚀 Steppppp {idx}: {step}")
            result = self.execute_task(step)
            print(f"✅ Result:\n{result}")

            reflection = self.reflect(result)
            print(f"🧠 Reflection: {reflection}")

            self.memory += f"\nStep {idx}: {step}\nResult: {result}\nReflection: {reflection}\n"

        print("\n🎉 All steps completed.")

# Example usage
if __name__ == "__main__":
    agent = SimpleAgenticAI()
    agent.run("Write a short guide about the benefits of walking daily")
