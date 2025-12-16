from rag.agent_cloud import agent_answer as cloudllm
from rag.agent_onprem import agent_answer as onpremllm

def run_test_query(query: str):
    print("\n" + "=" * 80)
    print(f"USER QUESTION: {query}")
    print("=" * 80)

    try:
        answer = cloudllm(query)
    except Exception as e:
        print("ERROR running agent:")
        print(e)
        return

    print("\nAGENT ANSWER:")
    print(answer)
    print("=" * 80)


def main():
    print("\n Running Agent Tests...\n")

    test_queries = [

          "Can you provide an analysis on the number of hubs in west region that are currently being supported on node NODE-101?",
          "Can you provide an analysis on the number of incidents for Chicago that have been closed with the Agent AutoMonitorX or NoiseReducer in the last week?",
          "How many times has hub HUB-D4 been affected this month?", 
          "What INC or CRQ is related to INC0325?",
          "When does the CR for this ticket INC0001 start and end?",
          "provide a graph on tickets created every month",

        #  "How many cancelled tickets do we have?",
        #  "How many tickets were created in West region last month?",
        #  "Show me similar tickets for video outage in Denver.",
        #  "Provide related historical worklogs for mobile tower issue.",
        #  "What is the number of HFC tickets in Seattle?",
        #  "Give me the context for customer outage in Colorado Springs."
     ]

    for q in test_queries:
        run_test_query(q)


if __name__ == "__main__":
    main()