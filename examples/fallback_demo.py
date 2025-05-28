#!/usr/bin/env python3
"""
LangChain Fallback Runnable Demo
===============================

Demonstrates the native LangChain fallback functionality in Omni-LLM.
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def demo_fallback_chains():
    """Demonstrate different fallback chain configurations."""
    
    print("🔗 LangChain Fallback Runnable Demo")
    print("=" * 50)
    
    # Example request configurations
    examples = [
        {
            "name": "🚀 Performance Optimized (Groq first)",
            "request": {
                "prompt": "What is the capital of France?",
                "fallback_strategy": "performance_optimized",
                "enable_fallback": True,
                "max_fallback_attempts": 3
            }
        },
        {
            "name": "💰 Cost Optimized (Cheapest first)",
            "request": {
                "prompt": "Explain machine learning in simple terms",
                "fallback_strategy": "cost_optimized", 
                "enable_fallback": True,
                "max_fallback_attempts": 3
            }
        },
        {
            "name": "🎯 Quality Optimized (Best models first)",
            "request": {
                "prompt": "Write a haiku about programming",
                "fallback_strategy": "quality_optimized",
                "enable_fallback": True,
                "max_fallback_attempts": 3
            }
        },
        {
            "name": "⚖️ Balanced (Best overall balance)",
            "request": {
                "prompt": "Tell me a joke about AI",
                "fallback_strategy": "balanced",
                "enable_fallback": True,
                "max_fallback_attempts": 3
            }
        },
        {
            "name": "📋 Priority Order (Default strategy)",
            "request": {
                "prompt": "How does LangChain fallback work?",
                "fallback_strategy": "priority_order",
                "enable_fallback": True,
                "max_fallback_attempts": 3
            }
        },
        {
            "name": "🎯 Specific Model with Fallback",
            "request": {
                "prompt": "Create a JSON response",
                "model_name": "gpt-4o-mini",
                "enable_fallback": True,
                "fallback_strategy": "cost_optimized",
                "structured_output_enabled": True,
                "structured_output_schema": {
                    "response": "string",
                    "model_used": "string",
                    "confidence": "number"
                }
            }
        }
    ]
    
    print("\n📝 Available Fallback Chain Examples:")
    print("-" * 40)
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['name']}")
        print(f"   Request: {json.dumps(example['request'], indent=2)}")
        
        # Show what this would do
        strategy = example['request'].get('fallback_strategy', 'balanced')
        model_name = example['request'].get('model_name')
        
        if model_name:
            print(f"   🔄 Primary: {model_name}")
            print(f"   🔄 Fallback Strategy: {strategy}")
            print(f"   🔄 Will fallback to other models if {model_name} fails")
        else:
            print(f"   🔄 Uses pre-configured '{strategy}' chain")
            
            if strategy == "performance_optimized":
                print(f"   🔄 Order: Groq (ultra-fast) → OpenAI → Anthropic")
            elif strategy == "cost_optimized":
                print(f"   🔄 Order: Groq (cheapest) → GPT-4o-mini → Claude Haiku")
            elif strategy == "quality_optimized":
                print(f"   🔄 Order: GPT-4o → Claude Sonnet → GPT-4o-mini")
            elif strategy == "balanced":
                print(f"   🔄 Order: GPT-4o-mini → Claude Haiku → Groq Llama")
            else:  # priority_order
                print(f"   🔄 Order: GPT-4o-mini → Claude Haiku → Groq → GPT-3.5")
    
    print("\n" + "=" * 50)
    print("🎯 Key Features of LangChain Fallback:")
    print("✅ Native with_fallbacks() runnable")
    print("✅ Automatic provider switching on failure")
    print("✅ Pre-configured strategy chains")
    print("✅ Custom fallbacks for specific models")
    print("✅ Cost/performance/quality optimization")
    print("✅ Zero manual retry logic needed")
    print("✅ Transparent fallback attempt tracking")
    
    print("\n🚀 Example Usage:")
    print("""
# Cost-optimized chain
curl -X POST http://localhost:8000/invoke \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: dev-key-12345" \\
  -d '{
    "prompt": "Hello!",
    "fallback_strategy": "cost_optimized",
    "enable_fallback": true,
    "max_fallback_attempts": 3
  }'

# Specific model with fallback
curl -X POST http://localhost:8000/invoke \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: dev-key-12345" \\
  -d '{
    "prompt": "Hello!",
    "model_name": "gpt-4o",
    "enable_fallback": true,
    "fallback_strategy": "performance_optimized"
  }'
""")


def show_fallback_chain_details():
    """Show detailed information about how fallback chains are constructed."""
    
    print("\n🔧 LangChain Fallback Chain Construction:")
    print("=" * 50)
    
    chains = {
        "cost_optimized": [
            "llama-3.1-8b-instant (Groq - Ultra cheap)",
            "llama-3.1-70b-versatile (Groq - Cheap)", 
            "gpt-4o-mini (OpenAI - Cost effective)"
        ],
        "performance_optimized": [
            "llama-3.1-8b-instant (Groq - Ultra fast)",
            "llama-3.1-70b-versatile (Groq - Very fast)",
            "mixtral-8x7b-32768 (Groq - Fast)"
        ],
        "quality_optimized": [
            "gpt-4o (OpenAI - Top quality)",
            "claude-3-5-sonnet-20241022 (Anthropic - Excellent)",
            "gpt-4o-mini (OpenAI - Very good)"
        ],
        "balanced": [
            "gpt-4o-mini (OpenAI - Great balance)",
            "claude-3-5-haiku-20241022 (Anthropic - Fast & good)",
            "llama-3.1-70b-versatile (Groq - Fast & capable)",
            "gemini-1.5-flash (Google - Balanced)"
        ]
    }
    
    for chain_name, models in chains.items():
        print(f"\n🔗 {chain_name.upper()} Chain:")
        print(f"   Created with: primary_model.with_fallbacks([fallback1, fallback2, ...])")
        for i, model in enumerate(models):
            if i == 0:
                print(f"   🎯 Primary:   {model}")
            else:
                print(f"   🔄 Fallback{i}: {model}")


if __name__ == "__main__":
    demo_fallback_chains()
    show_fallback_chain_details()