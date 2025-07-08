# Personas - Specialized AI Personalities for Enhanced Interactions

**Create and manage specialized AI personas with custom instructions, model preferences, and expertise domains**

The Personas system allows you to create and manage specialized AI personalities that transform how your AI assistant responds to different types of tasks. Each persona contains custom system instructions, model preferences, and metadata that shape the AI's behavior and expertise focus.

## Quick Start

**Create a new persona:**
```json
{
  "name": "personas_create",
  "arguments": {
    "id": "my_expert",
    "name": "My Technical Expert",
    "description": "Specialized in backend development and system architecture",
    "system_instructions": "You are a senior backend developer with expertise in Python, databases, and system design. Provide detailed technical explanations, focus on scalability and performance, and suggest best practices for production systems.",
    "model_name": "gemini-2.5-pro",
    "temperature": 0.3,
    "thinking_mode": "high",
    "tags": ["backend", "python", "architecture"]
  }
}
```

**Use the persona in any tool:**
```json
{
  "name": "chat",
  "arguments": {
    "prompt": "Help me design a microservices architecture for an e-commerce platform",
    "persona_id": "my_expert"
  }
}
```

## Core Concepts

### What are Personas?

Personas are specialized AI configurations that include:
- **System Instructions**: Custom prompts that define the AI's role, expertise, and behavior
- **Model Preferences**: Preferred models, temperature settings, and thinking modes
- **Metadata**: Tags, descriptions, and organizational information
- **Persistence**: Stored locally and reused across sessions

### Key Benefits

- **Specialized Expertise**: Create domain-specific AI assistants (security expert, Python developer, architect)
- **Consistent Behavior**: Maintain consistent AI responses across different sessions
- **Optimized Performance**: Use appropriate models and settings for specific use cases
- **Team Collaboration**: Share persona configurations across team members
- **Context Efficiency**: Pre-configured instructions reduce prompt repetition

## Available Tools

### 1. personas_create - Create New Personas

Create specialized AI personas with custom instructions and preferences.

**Required Parameters:**
- `id`: Unique identifier (alphanumeric + underscores)
- `name`: Display name for the persona
- `description`: Brief description of the persona's purpose
- `system_instructions`: Custom system prompt (10-10,000 characters)

**Optional Parameters:**
- `model_name`: Preferred model (e.g., "gemini-2.5-pro", "flash", "o3")
- `temperature`: Creativity level (0.0-1.0)
- `thinking_mode`: Reasoning depth (minimal, low, medium, high, max)
- `tags`: Array of tags for organization

**Example:**
```json
{
  "name": "personas_create",
  "arguments": {
    "id": "security_expert",
    "name": "Security Specialist",
    "description": "Expert in application security and vulnerability analysis",
    "system_instructions": "You are a cybersecurity expert specializing in application security. Analyze code for OWASP Top 10 vulnerabilities, provide specific remediation steps, and explain security implications. Focus on practical, actionable security improvements.",
    "model_name": "gemini-2.5-pro",
    "temperature": 0.2,
    "thinking_mode": "high",
    "tags": ["security", "vulnerabilities", "owasp"]
  }
}
```

### 2. personas_list - List Available Personas

View all available personas with optional filtering.

**Optional Parameters:**
- `tags_filter`: Filter by specific tags (array)
- `name_filter`: Filter by name (partial match)
- `limit`: Maximum number of results (1-100)
- `include_predefined`: Include built-in personas (default: true)

**Example:**
```json
{
  "name": "personas_list",
  "arguments": {
    "tags_filter": ["python", "backend"],
    "limit": 10
  }
}
```

### 3. personas_select - Select and Learn About a Persona

Get detailed information about a specific persona and learn how to use it.

**Required Parameters:**
- `id`: Persona identifier to select

**Optional Parameters:**
- `show_usage_examples`: Show usage examples (default: true)

**Example:**
```json
{
  "name": "personas_select",
  "arguments": {
    "id": "python_expert",
    "show_usage_examples": true
  }
}
```

### 4. personas_update - Update Existing Personas

Modify existing persona properties.

**Required Parameters:**
- `id`: Persona identifier to update
- One or more fields to update (name, description, system_instructions, model_name, temperature, thinking_mode, tags)

**Example:**
```json
{
  "name": "personas_update",
  "arguments": {
    "id": "my_expert",
    "system_instructions": "Updated instructions with new focus on cloud architecture",
    "tags": ["backend", "python", "cloud", "kubernetes"]
  }
}
```

### 5. personas_delete - Remove Personas

Delete a persona permanently.

**Required Parameters:**
- `id`: Persona identifier to delete

**Example:**
```json
{
  "name": "personas_delete",
  "arguments": {
    "id": "old_persona"
  }
}
```

## Built-in Personas

The system includes three professionally-configured personas ready for immediate use:

### 1. python_expert
- **Focus**: Python development, backend systems
- **Expertise**: Django, FastAPI, SQLAlchemy, PEP 8
- **Model**: Gemini 2.5 Pro with medium thinking
- **Best for**: Python code review, architecture decisions, backend development

### 2. system_architect
- **Focus**: Software architecture and technical decisions
- **Expertise**: Scalability, maintainability, performance
- **Model**: Gemini 2.5 Pro with high thinking
- **Best for**: System design, architectural reviews, technical planning

### 3. security_reviewer
- **Focus**: Security analysis and vulnerability assessment
- **Expertise**: OWASP Top 10, authentication, authorization
- **Model**: Gemini 2.5 Pro with high thinking
- **Best for**: Security audits, vulnerability analysis, secure coding

## Using Personas in Tools

### Adding Personas to Any Tool

Add the `persona_id` parameter to any tool call:

```json
{
  "name": "chat",
  "arguments": {
    "prompt": "Review this authentication implementation",
    "persona_id": "security_reviewer",
    "files": ["auth.py"]
  }
}
```

### Persona Integration Examples

**Code Review with Security Focus:**
```json
{
  "name": "codereview",
  "arguments": {
    "files": ["user_auth.py"],
    "persona_id": "security_reviewer"
  }
}
```

**Python-focused Analysis:**
```json
{
  "name": "analyze",
  "arguments": {
    "step": "Review this Django model implementation",
    "persona_id": "python_expert",
    "files": ["models.py"]
  }
}
```

**Architecture Planning:**
```json
{
  "name": "planner",
  "arguments": {
    "task": "Design a microservices architecture for user management",
    "persona_id": "system_architect"
  }
}
```

## Configuration and Storage

### Storage Location

Personas are stored locally in:
```
~/.zen_personas.json
```

### Configuration Options

The persona system can be configured through the `PersonaConfig` class:

```python
# Default configuration
max_personas: 100          # Maximum number of personas
cache_enabled: true        # Enable in-memory caching
backup_enabled: true       # Enable automatic backups
personas_storage_path: "~/.zen_personas.json"
```

### Backup and Recovery

**Automatic Backups:**
- Created in `.zen_personas_backups/` directory
- Timestamped backup files
- Automatic cleanup of old backups

**Manual Backup:**
```bash
# Backups are handled automatically by the system
# Files are stored in .zen_personas_backups/
```

## Best Practices

### Creating Effective Personas

1. **Clear Purpose**: Define specific expertise domains
2. **Detailed Instructions**: Provide comprehensive system instructions
3. **Appropriate Models**: Choose models that match the task complexity
4. **Consistent Behavior**: Test personas to ensure consistent responses
5. **Meaningful Tags**: Use descriptive tags for organization

### System Instructions Guidelines

**Good System Instructions:**
```
You are a senior Python developer with 10+ years of experience in backend systems. 
You specialize in Django, FastAPI, and database optimization. 

Your responses should:
- Follow PEP 8 and Python best practices
- Provide working code examples
- Explain performance implications
- Suggest testing strategies
- Consider security implications
```

**Avoid:**
- Vague instructions
- Conflicting directives
- Overly complex personalities
- Security-unsafe instructions

### Model Selection Guidelines

**Use Gemini 2.5 Pro for:**
- Complex analysis tasks
- Extended thinking requirements
- High-quality reasoning

**Use Flash for:**
- Quick responses
- Simple tasks
- Cost-sensitive operations

**Use O3 models for:**
- Logical reasoning
- Mathematical problems
- Structured analysis

### Temperature and Thinking Mode

**Temperature Settings:**
- `0.0-0.3`: Factual, technical, security-focused tasks
- `0.3-0.7`: Balanced creativity and accuracy
- `0.7-1.0`: Creative, brainstorming, idea generation

**Thinking Mode (Gemini only):**
- `minimal`: Quick responses, simple tasks
- `low`: Basic reasoning
- `medium`: Balanced analysis (recommended default)
- `high`: Complex problems, detailed analysis
- `max`: Maximum reasoning depth

## Advanced Usage

### Persona Workflows

**Development Workflow:**
```bash
# 1. Create domain-specific personas
personas_create -> python_expert, frontend_expert, devops_expert

# 2. Use throughout development cycle
chat (persona_id: python_expert) -> Design backend API
analyze (persona_id: frontend_expert) -> Review React components
codereview (persona_id: devops_expert) -> Check deployment scripts
```

**Security Review Workflow:**
```bash
# 1. Create security-focused persona
personas_create -> security_auditor

# 2. Apply to security tasks
secaudit (persona_id: security_auditor) -> Comprehensive security scan
codereview (persona_id: security_auditor) -> Security-focused code review
analyze (persona_id: security_auditor) -> Vulnerability analysis
```

### Multi-Persona Collaboration

Use different personas for different aspects of the same project:

```json
// Architecture planning
{
  "name": "planner",
  "arguments": {
    "task": "Design system architecture",
    "persona_id": "system_architect"
  }
}

// Security review
{
  "name": "codereview",
  "arguments": {
    "files": ["auth.py"],
    "persona_id": "security_reviewer"
  }
}

// Implementation details
{
  "name": "chat",
  "arguments": {
    "prompt": "Implement the authentication service",
    "persona_id": "python_expert"
  }
}
```

## Troubleshooting

### Common Issues

**Persona Not Found:**
- Check spelling of persona_id
- Use `personas_list` to see available personas
- Verify persona was created successfully

**Model Preferences Not Applied:**
- Check if model is available in your configuration
- Verify API keys for preferred models
- Review model restrictions in environment variables

**System Instructions Not Working:**
- Ensure instructions are clear and specific
- Check for conflicting directives
- Test with simple scenarios first

### Validation Errors

**ID Format:**
- Must be alphanumeric + underscores only
- 1-100 characters
- Will be converted to lowercase

**System Instructions:**
- 10-10,000 characters required
- No dangerous patterns allowed
- Must be meaningful and specific

**Tags:**
- Maximum 20 tags per persona
- Each tag maximum 50 characters
- Automatically deduplicated and normalized

## Integration with Other Tools

### Tool-Specific Behavior

**Chat Tool:**
- Persona instructions supplement the chat's collaborative nature
- Model preferences override chat defaults
- Temperature settings affect conversation tone

**Analysis Tools:**
- Persona expertise focuses analysis direction
- System instructions guide analysis methodology
- Model preferences affect analysis depth

**Workflow Tools:**
- Personas provide specialized workflow guidance
- Instructions shape task breakdown and approach
- Model settings optimize for workflow complexity

### Context and Memory

**Conversation Continuation:**
- Personas maintain consistency across continued conversations
- System instructions persist through conversation threads
- Model preferences remain active throughout the session

**Cross-Tool Persistence:**
- Personas work across all tool types
- Settings and instructions transfer between tools
- Consistent AI behavior throughout the session

## Performance Considerations

### Caching

- Personas are cached in memory for fast access
- Cache automatically refreshes when personas are modified
- TTL-based cache invalidation (30 minutes default)

### Storage

- JSON-based file storage for simplicity
- Automatic backup creation
- Efficient loading and saving operations

### Model Usage

- Persona model preferences can optimize token usage
- Appropriate model selection reduces costs
- Thinking mode settings balance quality and performance

## Security Considerations

### Input Validation

- Strict validation of all persona fields
- Prevention of prompt injection patterns
- Sanitization of system instructions

### Access Control

- Local file storage provides user-level isolation
- No network transmission of sensitive instructions
- User-controlled persona creation and management

### Best Practices

- Review system instructions for security implications
- Avoid embedding sensitive information in personas
- Use appropriate model restrictions for security-sensitive tasks

## Related Documentation

- **[Chat Tool Guide](tools/chat.md)** - Using personas with conversational AI
- **[Configuration Guide](configuration.md)** - Server configuration and model settings
- **[Advanced Usage Guide](advanced-usage.md)** - Advanced model usage patterns and workflows
- **[Tools Overview](tools/)** - Complete guide to all available tools and their persona integration