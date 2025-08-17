

import inspect
from langgraph.graph import StateGraph, END

from app.nodes import (
    code_execution_node,
    bug_report_node,
    memory_search_node,
    memory_filter_node,
    memory_generation_node,
    memory_modification_node,
    code_update_node,
    code_patching_node,
    error_router,
    memory_filter_router,
    memory_generation_router,
    memory_update_router
)

from app.model import AgentState

# --------------------
# BUILD AND COMPILE THE GRAPH
# --------------------

builder = StateGraph(AgentState)


builder.add_node('code_execution_node', code_execution_node)
builder.add_node('bug_report_node', bug_report_node)
builder.add_node('memory_search_node', memory_search_node)
builder.add_node('memory_filter_node', memory_filter_node)
builder.add_node('memory_modification_node', memory_modification_node)
builder.add_node('memory_generation_node', memory_generation_node)
builder.add_node('code_update_node', code_update_node)
builder.add_node('code_patching_node', code_patching_node)



builder.set_entry_point('code_execution_node')
builder.add_conditional_edges('code_execution_node', error_router)
builder.add_edge('bug_report_node', 'memory_search_node')
builder.add_conditional_edges('memory_search_node', memory_filter_router)
builder.add_conditional_edges('memory_filter_node', memory_generation_router)
builder.add_edge('memory_generation_node', 'code_update_node')
builder.add_conditional_edges('memory_modification_node', memory_update_router)

builder.add_edge('code_update_node', 'code_patching_node')
builder.add_edge('code_patching_node', 'code_execution_node')


agent_graph = builder.compile()


def execute_self_healing_code_system(function, arguments, function_string):
    """
    Executes the self-healing workflow.
    
    Args:
        function: The Python callable function.
        arguments: The arguments for the function.
        function_string: The string representation of the function's code.
    """
    initial_state = AgentState(
        error=False,
        function=function,
        function_string=function_string,  # Use the provided string directly
        arguments=arguments,
        error_description='',
        new_function_string='',
        bug_report='',
        memory_search_results=[],
        memory_ids_to_update=[]
    )
    
    return agent_graph.invoke(initial_state)

if __name__ == '__main__':
    # You can use this block for local testing
    
    # Test Case 1: Division with zero (triggers new memory)
    def test_division_by_zero(a, b):
        return a / b

    print("***********************************")
    print("** Testing Division by Zero      **")
    print("** (Should create new memory)    **")
    print("***********************************")
    execute_self_healing_code_system(test_division_by_zero, [10, 0], inspect.getsource(test_division_by_zero))
    
    # Test Case 2: Division by Zero (triggers memory modification)
    def perform_division(numerator, denominator):
        return numerator / denominator

    print("\n**************************************")
    print("** Testing Similar Division by Zero **")
    print("** (Should modify existing memory)  **")
    print("**************************************")
    execute_self_healing_code_system(perform_division, [20, 0], inspect.getsource(perform_division))
    
    # Test Case 3: Key Error in Dictionary
    def get_dict_value(data_dict, key):
        return data_dict[key]

    print("\n***********************************")
    print("** Testing Dictionary Key Error  **")
    print("***********************************")
    execute_self_healing_code_system(get_dict_value, [{"name": "Alice", "age": 30}, "city"], inspect.getsource(get_dict_value))
    
    # Test Case 4: Basic Logic Error (Beginner)
    def calculate_average(numbers):
        total = 0
        for num in numbers:
            total += num
        # Bug: This should be len(numbers)
        return total / 0

    print("\n***************************************")
    print("** Testing Basic Logic Error         **")
    print("***************************************")
    execute_self_healing_code_system(calculate_average, [[10, 20, 30]], inspect.getsource(calculate_average))

    # Test Case 5: Data Type Mismatch (Intermediate)
    def concatenate_strings(s1, s2):
        return s1 + " " + s2.upper()

    print("\n*******************************************")
    print("** Testing Data Type Mismatch            **")
    print("*******************************************")
    execute_self_healing_code_system(concatenate_strings, ["hello", 123], inspect.getsource(concatenate_strings))

    # Test Case 6: Edge Case (Advanced)
    def get_first_element(my_list):
        return my_list[0]

    print("\n***************************************")
    print("** Testing Edge Case (Empty List)    **")
    print("***************************************")
    execute_self_healing_code_system(get_first_element, [[]], inspect.getsource(get_first_element))
    
    # Test Case 7: Recursive Function Bug (Expert)
    def sum_to_n(n):
        if n <= 0:
            return 0
        # Bug: This causes infinite recursion
        return n + sum_to_n(n)

    print("\n*******************************************")
    print("** Testing Recursive Function Bug        **")
    print("*******************************************")
    execute_self_healing_code_system(sum_to_n, [5], inspect.getsource(sum_to_n))


    # Test Case 8: Floating Point Imprecision (Subtle Logic Bug)
    def check_sum_of_floats(numbers):
        total = 0.0
        for num in numbers:
            total += num
        if total == 0.3:
            return "Sum is 0.3"
        return "Sum is not 0.3"

    print("\n*******************************************")
    print("** Testing Floating Point Imprecision    **")
    print("*******************************************")
    execute_self_healing_code_system(check_sum_of_floats, [[0.1, 0.1, 0.1]], inspect.getsource(check_sum_of_floats))

    # Test Case 9: Incorrect API Usage (Library-Specific Error)
    from datetime import datetime, timedelta
    def add_time_to_date(start_date, days):
        # This function should add days to a date, but has a bug
        return start_date + timedelta(days)

    print("\n*******************************************")
    print("** Testing Incorrect API Usage           **")
    print("*******************************************")
    execute_self_healing_code_system(add_time_to_date, [datetime(2024, 1, 1), '5'], inspect.getsource(add_time_to_date))

