# Cyber-Security Code Analyzer

![Project Logo](assets/cyber.png)

A comprehensive cybersecurity analysis tool that combines static code analysis with AI-powered security scanning to identify vulnerabilities in your codebase. The tool leverages Semgrep for static analysis and integrates with cloud providers like Azure and GCP for comprehensive security scanning.

## Features

- **Static Code Analysis**: Identify security vulnerabilities in Python code
- **AI-Powered Scanning**: Advanced analysis using AI to detect complex security issues
- **Multi-Cloud Support**: Integration with Azure and GCP security tools
- **Dockerized Environment**: Easy setup and deployment using Docker
- **RESTful API**: Simple integration with CI/CD pipelines

## Prerequisites

- Docker and Docker Compose
- Git
- (Optional) Cloud provider credentials (Azure/GCP) for full functionality

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/ed-donner/cyber.git
cd cyber
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key
SEMGREP_APP_TOKEN=your_semgrep_app_token

# Optional: Cloud Provider Configuration
# AZURE_CLIENT_ID=your_azure_client_id
# AZURE_CLIENT_SECRET=your_azure_client_secret
# GCP_PROJECT_ID=your_gcp_project_id
# GCP_CREDENTIALS=path_to_your_gcp_credentials.json
```

### 3. Build and Run with Docker

```bash
docker-compose up --build
```

This will:
1. Build the frontend and backend containers
2. Start the FastAPI server on port 8000
3. Serve the Next.js frontend

## Usage

### API Endpoints

- `POST /api/analyze` - Analyze code for security vulnerabilities
  - Request body: `{"code": "your_python_code_here"}`
  - Returns: JSON with security analysis results

- `GET /health` - Health check endpoint
- `GET /network-test` - Test network connectivity
- `GET /semgrep-test` - Test Semgrep integration

### Web Interface

After starting the application, access the web interface at:

```
http://localhost:3000
```

## Development

### Project Structure

```
cyber/
├── backend/           # FastAPI server and security analysis logic
├── frontend/          # Next.js frontend application
├── terraform/         # Infrastructure as Code for cloud deployment
├── .env.example       # Example environment variables
└── Dockerfile         # Multi-stage Dockerfile for production
```

### Running Locally (Development)

1. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -e .
   uvicorn server:app --reload
   ```

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Deployment

### Cloud Deployment

The project includes Terraform configurations for deploying to Azure and GCP. See the `terraform/` directory for details.

### Building for Production

```bash
docker build -t cyber-security-analyzer .
docker run -p 8000:8000 --env-file .env cyber-security-analyzer
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue or contact ed@edwarddonner.com

---

_If you're looking at this in Cursor, right-click on the filename in the Explorer and select "Open Preview" for better formatting._