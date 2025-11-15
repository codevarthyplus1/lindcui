# Contributing to KVM Cluster Management System

Thank you for your interest in contributing to this project!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/lindcui.git
   cd lindcui
   ```

3. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

## Project Structure

```
lindcui/
├── backend/          # Python FastAPI backend
│   ├── api/         # API routes
│   ├── models/      # Database models
│   ├── services/    # Business logic
│   └── main.py      # Application entry point
├── frontend/         # React TypeScript frontend
│   └── src/
│       ├── components/  # React components
│       └── services/    # API client
└── README.md
```

## Coding Standards

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints
- Write docstrings for all functions
- Run tests before committing

### TypeScript (Frontend)
- Use TypeScript strict mode
- Follow React best practices
- Use functional components with hooks
- Keep components focused and reusable

## Testing

### Backend
```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend
```bash
cd frontend
npm test
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## Issues

- Check existing issues before creating new ones
- Provide detailed reproduction steps for bugs
- Include system information and error messages
- Use issue templates when available

## Feature Requests

We welcome feature requests! Please:
- Explain the use case
- Describe the proposed solution
- Consider alternative approaches

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
