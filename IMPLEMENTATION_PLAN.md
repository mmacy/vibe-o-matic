# Implementation Plan: Simplified Responses API Integration

## Date
2025-11-14

## Objective
Simplify the GPT-5 Responses API implementation in `orchestration.ts` to eliminate regressions and reduce complexity while maintaining full functionality.

## Issues to Address

### Critical Issues
1. **Unnecessary message stringification** - Converting structured messages to concatenated strings loses context
2. **Incorrect tool result handling** - Using `role: 'tool'` instead of proper Responses API format
3. **Massive code duplication** - 200+ lines duplicated between GPT-5 and GPT-4 paths
4. **Excessive streaming complexity** - Overly complex Map-based tracking for function calls

### Performance Issues
- String concatenation overhead on every iteration
- Multiple unnecessary JSON.stringify() operations
- Increased bundle size from code duplication

## Solution Approach

### Strategy: Unified Message Handling with Minimal Branching

The Responses API supports structured messages similar to Chat Completions. We'll:

1. **Keep messages structured** - Don't stringify them
2. **Create converter functions** - Small, focused adapters for API differences
3. **Share common logic** - Extract tool execution, audit tracking, and streaming into shared code
4. **Branch only at API boundaries** - Only differ where APIs actually differ

### Key Insight

Both APIs support:
- ✅ Structured messages with roles
- ✅ Tool/function calling
- ✅ Streaming responses
- ✅ Sequential tool calls

Main differences:
- Input parameter name: `messages` vs `input`
- Tool structure: nested vs flat
- Token parameter: `max_tokens` vs `max_output_tokens`
- Response format: `choices[0].message` vs `output` array
- Streaming events: different event types

## Implementation Steps

### Step 1: Create Message Converter (if needed)
Since Responses API accepts structured messages, we may only need to handle tool results differently:

```typescript
function convertMessagesForResponsesAPI(messages: ChatCompletionMessageParam[]) {
  // Most messages pass through as-is
  // Only convert tool results to function_call_output format if needed
  return messages.map(msg => {
    if (msg.role === 'tool') {
      return {
        type: 'function_call_output',
        call_id: msg.tool_call_id,
        output: msg.content
      }
    }
    return msg
  })
}
```

**UPDATE**: Based on research, Responses API may accept the standard format. We'll try the simplest approach first - passing messages directly with minimal conversion.

### Step 2: Create Shared Tool Execution Logic
Extract the duplicated tool call execution and audit tracking:

```typescript
function processToolCall(
  toolCall: { id: string; type: 'function'; function: { name: string; arguments: string } },
  diceAudit: GMResponse['diceAudit'],
  createdCharacters: CreateCharacterInput[]
): { role: 'tool'; tool_call_id: string; content: string } {
  const result = executeToolCall(toolCall.function.name, toolCall.function.arguments)

  // Audit tracking logic (shared)
  try {
    const resultObj = JSON.parse(result)
    const argsObj = JSON.parse(toolCall.function.arguments)

    if (!resultObj.error) {
      if (toolCall.function.name === 'roll_dice') {
        diceAudit.push({
          source: argsObj.source || 'Unknown',
          action: argsObj.action || 'roll',
          target: argsObj.target,
          total: resultObj.total,
          expr: resultObj.normalized_expr || argsObj.expr,
        })
      }
      if (toolCall.function.name === 'create_character' && resultObj.character) {
        createdCharacters.push(resultObj.character)
      }
    }
  } catch {
    // Ignore parse errors
  }

  return {
    role: 'tool',
    tool_call_id: toolCall.id,
    content: result,
  }
}
```

### Step 3: Simplify Main Flow
Use a simple conditional for API selection, but keep the rest of the logic unified:

```typescript
// Determine API to use
const isGPT5Model = model.toLowerCase().includes('gpt-5')

// Make API call (only difference here)
const response = isGPT5Model
  ? await client.responses.create({
      model,
      input: currentMessages,  // Try structured messages first
      tools: convertToolsForResponsesAPI(tools),
      max_output_tokens: settings?.max_tokens,
      reasoning: { effort: 'medium' },
      parallel_tool_calls: false,
      stream: !!onStreamChunk,
    })
  : await client.chat.completions.create({
      model,
      messages: currentMessages,
      tools: tools,
      max_tokens: settings?.max_tokens,
      temperature: settings?.temperature,
      parallel_tool_calls: false,
      stream: !!onStreamChunk,
    })

// Unified response handling
const result = isGPT5Model
  ? extractFromResponsesAPI(response)
  : extractFromChatCompletion(response)

// Rest of logic is shared
```

### Step 4: Simplify Streaming
Create a unified streaming handler that works with both APIs:

```typescript
async function handleStreamingResponse(response, onStreamChunk, isGPT5) {
  const accumulated = {
    text: '',
    toolCalls: []
  }

  for await (const chunk of response) {
    // Different parsing based on API, but same accumulation logic
    const delta = isGPT5
      ? parseResponsesAPIChunk(chunk)
      : parseChatCompletionChunk(chunk)

    if (delta.text) {
      accumulated.text += delta.text
      onStreamChunk(delta.text)
    }

    if (delta.toolCall) {
      accumulateToolCall(accumulated.toolCalls, delta.toolCall)
    }
  }

  return accumulated
}
```

## Expected Outcomes

### Code Reduction
- Remove ~150 lines of duplicated code
- Simpler logic = fewer bugs
- Easier to maintain

### Performance Improvements
- Eliminate string concatenation overhead
- Reduce JSON operations
- Faster execution

### Correctness
- Proper tool call handling
- Correct conversation context
- Multi-turn conversations work reliably

## Testing Strategy

1. Run existing test suite: `npm test`
2. Manual testing with GPT-5 model (if available)
3. Verify tool calls work in multi-turn conversations
4. Test streaming and non-streaming modes
5. Verify dice audit and character creation still work

## Rollback Plan

If issues arise:
1. Commit is atomic and can be reverted
2. Previous PR branch still exists
3. Can cherry-pick specific fixes if needed

## Implementation Notes

- Preserve all existing functionality
- Maintain backward compatibility with GPT-4 models
- Keep the same external API (`getGMResponse` interface)
- Use TypeScript types to catch errors early
- Add comments explaining API differences where needed

## Success Criteria

✅ All existing tests pass
✅ Code is <100 lines shorter
✅ No duplicated logic between GPT-4 and GPT-5 paths
✅ Tool calls work correctly in both APIs
✅ Streaming works correctly
✅ Performance is equal or better
