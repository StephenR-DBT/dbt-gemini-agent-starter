# dbt-gemini-agent

A powerful AI agent built with Google's Agent Development Kit (ADK) that provides intelligent assistance for dbt (data build tool) projects. The agent combines local dbt compilation capabilities with cloud-based dbt platform integration through MCP (Model Context Protocol) tools.

## 🚀 Features

### Core Capabilities
- **dbt Compilation & Analysis**: Compile dbt projects locally and analyze JSON logs for errors and issues
- **dbt Platform Integration**: Connect to dbt Cloud/Platform via MCP for advanced operations
- **Intelligent Problem Detection**: Automatically identify and suggest fixes for dbt compilation errors
- **Data Modeling Analysis**: Analyze data modeling patterns and suggest improvements
- **Multi-LLM Support**: Works with Gemini, OpenAI, Claude, and other LLM providers via LiteLLM

### Tools & Subagents
- **dbt_compile**: Local dbt compilation with detailed JSON log analysis
- **dbt_mcp_toolset**: Cloud-based dbt platform operations via MCP
- **dbt_model_analyzer**: Specialized subagent for data modeling analysis

## 📋 Prerequisites

- Python 3.10+
- dbt CLI installed and configured
- Google Cloud Project (for ADK)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dbt-gemini-agent
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run**:
   ```bash
   adk web # will load at localhost:8000 by default
   ```

## 🏗️ Project Structure

```
dbt-gemini-agent/
├── dbt_data_scientist/           # Main agent package
│   ├── agent.py                  # Root agent configuration
│   ├── prompts.py               # Agent instructions and prompts
│   ├── tools/                   # Agent tools
│   │   ├── dbt_compile.py       # Local dbt compilation tool
│   │   └── dbt_mcp.py          # MCP toolset for dbt platform
│   ├── sub_agents/              # Specialized subagents
│   │   └── dbt_model_analyzer.py # Data modeling analysis agent
│   ├── test_all_tools.py        # Comprehensive test suite
│   └── quick_mcp_test.py        # MCP connection test
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## 🚀 Usage

### Basic Usage

### Testing the Setup

1. **Test MCP Connection**:
   ```bash
   python dbt_data_scientist/quick_mcp_test.py
   ```

2. **Run Comprehensive Tests**:
   ```bash
   python dbt_data_scientist/test_all_tools.py
   ```

### Example Interactions

#### Compile and Analyze dbt Project
```
User: "Compile my dbt project and find any issues"
Agent: 
1. Runs dbt compile --log-format json
2. Analyzes JSON logs for errors
3. Provides specific error locations and suggested fixes
```

#### dbt Platform Operations
```
User: "Show me my dbt Cloud jobs"
Agent: Uses MCP tools to query dbt Cloud API and display job information
```

#### Data Modeling Analysis
```
User: "Analyze my data modeling approach"
Agent: Delegates to dbt_model_analyzer subagent for specialized analysis
```

## 🔧 Tools Reference

### dbt_compile Tool
- **Purpose**: Compiles dbt projects locally and returns structured JSON logs
- **Input**: Any string (triggers compilation)
- **Output**: Dictionary with returncode and parsed logs
- **Features**: 
  - Automatic error detection
  - Structured log parsing
  - Environment variable configuration

### dbt_mcp_toolset
- **Purpose**: Provides access to dbt Cloud/Platform via MCP
- **Features**:
  - Job management
  - Environment operations
  - Project metadata access
  - Real-time monitoring

### dbt_model_analyzer Subagent
- **Purpose**: Specialized analysis of data modeling patterns
- **Capabilities**:
  - Schema pattern detection
  - Modeling best practices analysis
  - Performance recommendations

## 🧪 Testing

The project includes comprehensive testing utilities:

### Quick MCP Test
```bash
python dbt_data_scientist/quick_mcp_test.py
```
- Tests MCP connection
- Validates authentication
- Lists available tools

### Full Test Suite
```bash
python dbt_data_scientist/test_all_tools.py
```
- Tests all tools and subagents
- Validates environment configuration
- Ensures proper cleanup

## 🔍 Troubleshooting

### Common Issues

1. **"No module prompts" error**:
   - Ensure you're running from the correct directory
   - Check that all imports use relative paths

2. **MCP connection errors**:
   - Verify environment variables are set correctly
   - Check dbt Cloud/Platform credentials
   - Ensure network connectivity

3. **dbt compilation errors**:
   - Verify DBT_PROJECT_LOCATION points to valid dbt project
   - Check DBT_EXECUTABLE path
   - Ensure dbt project is properly configured

4. **Async generator cleanup warnings**:
   - The test suite includes proper cleanup
   - These warnings are typically harmless but indicate connection cleanup issues


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Happy data modeling with AI! 🚀📊**
