import { describe, it, expect } from 'vitest'
import { aggregateOutputText, extractToolCalls } from '../src/lib/openai/client'

describe('aggregateOutputText', () => {
  it('should aggregate text from output items', () => {
    const output = [
      { type: 'text', text: 'Hello' },
      { type: 'text', text: 'World' },
    ]

    const result = aggregateOutputText(output)
    expect(result).toContain('Hello')
    expect(result).toContain('World')
  })

  it('should handle empty output', () => {
    const result = aggregateOutputText([])
    expect(result).toBe('')
  })

  it('should handle mixed content types', () => {
    const output = [
      { type: 'text', text: 'Hello' },
      { type: 'other', data: 'ignored' },
      { type: 'text', text: 'World' },
    ]

    const result = aggregateOutputText(output)
    expect(result).toContain('Hello')
    expect(result).toContain('World')
    expect(result).not.toContain('ignored')
  })
})

describe('extractToolCalls', () => {
  it('should extract function calls', () => {
    const output = [
      {
        type: 'function_call',
        id: 'call_123',
        name: 'roll_dice',
        arguments: '{"expr":"1d20","source":"Fighter","action":"attack"}',
      },
    ]

    const calls = extractToolCalls(output)
    expect(calls).toHaveLength(1)
    expect(calls[0].name).toBe('roll_dice')
    expect(calls[0].id).toBe('call_123')
  })

  it('should handle nested function structure', () => {
    const output = [
      {
        type: 'tool_call',
        id: 'call_456',
        function: {
          name: 'roll_dice',
          arguments: '{"expr":"1d6"}',
        },
      },
    ]

    const calls = extractToolCalls(output)
    expect(calls).toHaveLength(1)
    expect(calls[0].name).toBe('roll_dice')
  })

  it('should handle empty output', () => {
    const calls = extractToolCalls([])
    expect(calls).toHaveLength(0)
  })
})
