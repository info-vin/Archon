from typing import Tuple

class EchoAgent:
    """
    A simple agent for testing purposes.
    It has a single asynchronous method `arun` that echoes the input.
    """

    async def arun(self, query: str) -> Tuple[bool, str]:
        """
        Simply returns the query, simulating an asynchronous operation.
        This method is the target for mocking in tests.
        """
        print(f"EchoAgent received: {query}")
        return True, f"Echo: {query}"
