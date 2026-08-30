import sys

with open("enduser-ui-fe/src/features/manager/machines/approvalMachine.ts", "r") as f:
    content = f.read()

search_block = """
           }
           const proposal = context.proposals.find(p => p.id === id)!;
           return {
"""

replace_block = """
           }
           const proposalMap = new Map(context.proposals.map(p => [p.id, p]));
           const proposal = proposalMap.get(id)!;
           return {
"""

content = content.replace(search_block, replace_block)

search_block2 = """
    generatingReason: {
      invoke: {
        src: 'generateAiReason',
        input: ({ context }) => {
           const proposal = context.proposals.find(p => p.id === context.selectedId)!;
           return { proposal };
"""

replace_block2 = """
    generatingReason: {
      invoke: {
        src: 'generateAiReason',
        input: ({ context }) => {
           const proposalMap = new Map(context.proposals.map(p => [p.id, p]));
           const proposal = proposalMap.get(context.selectedId!)!;
           return { proposal };
"""

content = content.replace(search_block2, replace_block2)

with open("enduser-ui-fe/src/features/manager/machines/approvalMachine.ts", "w") as f:
    f.write(content)
