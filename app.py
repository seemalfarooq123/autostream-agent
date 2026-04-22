from graph import build_graph

graph = build_graph()

state = {"input": "", "lead": {}}

print("🚀 AutoStream AI Agent Ready!")

while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Agent: Goodbye! 👋")
        break

    state["input"] = user_input

    result = graph.invoke(state)


    # 🔥 IMPORTANT FIX (this was missing before)
    if result is not None:
        state = result

    # Show response
    if state.get("response") is not None:
        print("Agent:", state["response"])

    # Handle lead flow
    while state.get("ask"):
        answer = input("Agent: " + state["ask"] + " ")

        if "name" not in state["lead"]:
            state["lead"]["name"] = answer
        elif "email" not in state["lead"]:
            state["lead"]["email"] = answer
        elif "platform" not in state["lead"]:
            state["lead"]["platform"] = answer

        state = graph.invoke(state)

# 🔥 STOP AFTER COMPLETION
        if state.get("intent") == "done":
            if "response" in state:
                print("Agent:", state["response"])
            break
        if "response" in state:
            print("Agent:", state["response"])
        if "ask" not in state:
            break