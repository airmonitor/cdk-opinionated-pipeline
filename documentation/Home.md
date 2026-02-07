[![Python Version](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![AWS CDK](https://img.shields.io/badge/AWS%20CDK-v2-orange.svg)](https://aws.amazon.com/cdk/)
[![security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen.svg)](https://github.com/pre-commit/pre-commit)
[![ssort](https://img.shields.io/badge/ssort-0.14.0-green.svg)](https://github.com/bwhmather/ssort)
[![ruff](https://img.shields.io/badge/ruff-v0.11.9-blue.svg)](https://github.com/charliermarsh/ruff-pre-commit)
[![mypy](https://img.shields.io/badge/mypy-v1.15.0-blue.svg)](https://github.com/pre-commit/mirrors-mypy)
[![shed](https://img.shields.io/badge/shed-2024.10.1-green.svg)](https://github.com/Zac-HD/shed)
[![xenon](https://img.shields.io/badge/xenon-v0.9.3-blue.svg)](https://github.com/rubik/xenon)
[![gitleaks](https://img.shields.io/badge/gitleaks-v8.26.0-red.svg)](https://github.com/gitleaks/gitleaks)
[![bandit](https://img.shields.io/badge/bandit-1.8.3-yellow.svg)](https://github.com/PyCQA/bandit)
[![hadolint](https://img.shields.io/badge/hadolint-v2.13.1--beta-blue.svg)](https://github.com/hadolint/hadolint)
[![detect-secrets](https://img.shields.io/badge/detect--secrets-v1.5.0-yellow.svg)](https://github.com/Yelp/detect-secrets)
[![uv-secure](https://img.shields.io/badge/uv--secure-0.9.0-blue.svg)](https://github.com/owenlamont/uv-secure)
[![mdformat](https://img.shields.io/badge/mdformat-0.7.22-green.svg)](https://github.com/hukkin/mdformat)

# Home

## Introduction

## Table of Contents

## Architecture

## Overview

### Purpose

### Target Audience

### Business Value

## Use Case

## Stories (user, operational, and technical)

### User Stories

### Operational Stories

### Technical Stories

## Requirements

### Functional

### Non-functional

## Monitoring

### Monitoring Best Practices

### Key Metrics

### Performance Architecture

### Deployment Performance Optimization

### Performance Monitoring and Optimization

#### Performance Optimization Process

## Security & Privacy

### Security Controls Matrix

## Scalability

## Availability

## Architecture/Infrastructure

### Core Architecture Principles

### CI/CD Pipeline

### Storage and Configuration

### Security Controls

### Monitoring and Observability

### Architecture Diagrams

#### CI/CD Pipeline

#### High-Level Architecture Overview

#### CI/CD Pipeline Flow

### AWS Services Used

## Architectural Decision Record 1: Multi-Account Strategy

### Context

The infrastructure needs to support multiple environments (dev, acc, prod) with appropriate isolation and security.

### Decision

Implement a multi-account strategy with separate AWS accounts for each environment:

- Development:
- Acceptance:
- Production:

### Consequences

- **Positive**:

  - Strong isolation between environments
  - Ability to apply different security controls per environment
  - Clear cost attribution per environment
  - Reduced blast radius for security incidents

- **Negative**:

  - Increased complexity in managing multiple accounts
  - Need for cross-account role assumption
  - Additional IAM configuration required

## Architectural Decision Record 2: Infrastructure as Code with AWS CDK

### Context

The infrastructure needs to be reproducible, version-controlled, and maintainable.

### Decision

Use AWS CDK with Python to define all infrastructure components as code.

### Consequences

- **Positive**:

  - Infrastructure defined as high-level code rather than CloudFormation templates
  - Type safety and validation through Python and Pydantic
  - Ability to use software development practices (testing, version control)
  - Reusable components and constructs

- **Negative**:

  - Learning curve for team members not familiar with CDK
  - Need to keep CDK dependencies updated
  - Potential for drift between CDK code and deployed resources

## Implementation

### Technology Stack

#### Core Technologies

- **Python 3.13+**: Core programming language for CDK code with type hints and modern features
- **AWS CDK v2**: Infrastructure as Code framework with L2 and L3 constructs
- **AWS CodePipeline V2**: CI/CD orchestration with enhanced features for triggers and notifications

#### Security and Compliance Tools

- **CDK NAG**: Infrastructure security and compliance validation
- **Bandit**: Python security linter
- **Gitleaks**: Secret detection in code repositories

#### Development and Testing Tools

- **Pytest**: Testing framework for infrastructure tests
- **Pre-commit**: Automated code quality and security checks
- **Ruff**: Fast Python linter
- **Mypy**: Static type checking for Python
- **Diagrams**: Architecture diagram generation using Python

### Git Repositories and Dependencies

- **Main Repository**:
- **Related Projects**:

### Key Implementation Details

#### Pipeline Structure

The CI/CD pipeline is defined in `cdk/stacks/pipeline_stack.py` and implements:

1. **Multi-Environment Deployment**: Progressive deployment across dev, acc, and prod
2. **Security Gates**: Code quality, vulnerability scanning, and image validation
3. **Cross-Account Deployment**: Secure deployment to isolated accounts
4. **Notifications**: Real-time alerts for pipeline events

### Implementation Best Practices

1. **Type Safety**: Use of Pydantic models for configuration validation
2. **Modular Design**: Separation of concerns with dedicated stacks and stages
3. **Reusable Components**: Leveraging CDK constructs for standardization
4. **Comprehensive Testing**: Infrastructure tests for all stacks
5. **Documentation**: Detailed documentation with architecture diagrams
6. **Security by Default**: Security controls integrated at every layer

## CI/CD Pipeline Flow

The CI/CD pipeline consists of the following stages:

1. **Source**: Retrieves code from the Git repository
2. **Artefact**: Creates SSM parameters for configuration
3. **Code Quality**: Runs code quality checks
4. **Infrastructure Tests**: Tests infrastructure code
5. **Plugins**: Deploys environment-specific plugins
6. **Shared Resources**: Deploys shared infrastructure resources
   - Notifications
   - Governance

The pipeline is triggered by:

- Push to the main branch
- Pull requests
- Git tags

## Operational Guidelines

This section provides comprehensive guidance for operating and maintaining the infrastructure,
including deployment procedures, monitoring strategies, troubleshooting approaches, and maintenance best practices.

### Deployment Workflow

The infrastructure supports a robust deployment workflow with multiple environments and security gates.
For detailed step-by-step deployment instructions, see [Deployment.md](Deployment.md).

#### Deployment Strategy

The deployment strategy follows a progressive model:

1. **Development (Dev)**: Initial deployment for testing and validation

Each environment is isolated in its own AWS account with appropriate security controls and access restrictions.

### Monitoring and Observability

The infrastructure includes comprehensive monitoring and observability capabilities to ensure operational excellence.

#### Budget Monitoring

Budget alerts are configured to notify when spending approaches defined thresholds:

- **Warning Threshold**: 80% of monthly budget
- **Critical Threshold**: 95% of monthly budget

Budget alerts are sent to the finance team and infrastructure owners.

## Troubleshooting

This section provides guidance for troubleshooting common issues with the infrastructure.

#### Pipeline Failures

If a pipeline stage fails:

1. **Check CodeBuild Logs**

2. **Examine CloudWatch Logs**:
   Navigate to the CloudWatch Logs console and check the log group for the failed build.

3. **Common Pipeline Issues and Solutions**:

   | Issue                 | Possible Cause           | Solution                                    |
   | --------------------- | ------------------------ | ------------------------------------------- |
   | Source stage failure  | Git connectivity issue   | Check CodeStar connection status            |
   | Build stage failure   | Missing dependencies     | Update requirements.txt                     |
   | Test stage failure    | Failed assertions        | Fix code or update test expectations        |
   | Deploy stage failure  | Permission issues        | Verify IAM roles and trust relationships    |
   | Security scan failure | Vulnerabilities detected | Address vulnerabilities or update threshold |

#### Access and Permission Issues

For access and permission issues:

1. **Cross-Account Access**:

   - Verify trust relationships between accounts
   - Check role assumption policies
   - Ensure temporary credentials are not expired

2. **Resource Access**:

   - Review IAM policies for least privilege
   - Check resource-based policies (S3, ECR)
   - Verify VPC endpoint configurations if applicable

### Maintenance Procedures

Regular maintenance is essential for ensuring the security, reliability, and efficiency of the infrastructure.

#### Suggested scheduled maintenance

| Frequency   | Task                   | Description                        |
| ----------- | ---------------------- | ---------------------------------- |
| Weekly      | Security patching      | Apply critical security patches    |
| Monthly     | Dependency updates     | Update non-critical dependencies   |
| Quarterly   | Cost optimization      | Review and optimize resource usage |
| Bi-annually | Architecture review    | Evaluate and improve architecture  |
| Annually    | Disaster recovery test | Test recovery procedures           |

#### Documentation Maintenance

Keep documentation up-to-date:

1. **Update after changes**: Update documentation when infrastructure changes
2. **Version control**: Maintain documentation in version control
3. **Review cycle**: Conduct quarterly documentation reviews
4. **Feedback loop**: Incorporate user feedback into documentation

#### Backup and Retention

The infrastructure implements the following backup and retention policies:

- **S3 Artifacts**: Lifecycle rules transition to Glacier after 30 days
- **CloudWatch Logs**: Retain for 90 days
- **CloudTrail Logs**: Retain for 365 days

## Security Guidelines

This section provides comprehensive guidance on security best practices, compliance requirements, and security controls
implemented in the infrastructure.

### Security Architecture

The security architecture follows a defense-in-depth approach with multiple layers of protection:

1. **Identity and Access Management**: Fine-grained access control with least privilege
2. **Infrastructure Security**: Secure configuration of AWS services
3. **Data Protection**: Encryption at rest and in transit
4. **Monitoring and Detection**: Continuous monitoring for security events
5. **Incident Response**: Procedures for responding to security incidents

### Security Best Practices

#### Identity and Access Management

- **Least Privilege Access**: Always use the minimum permissions required for each role
- **Role-Based Access Control**: Assign permissions based on job functions
- **Temporary Credentials**: Use short-lived credentials with automatic rotation
- **Multi-Factor Authentication**: Require MFA for AWS console access
- **Cross-Account Access**: Use secure role assumption for cross-account operations

#### Data Protection

- **Encryption at Rest**: Encrypt all data stored in S3 buckets

#### Monitoring and Detection

- **Audit Logging**: Enable and review AWS CloudTrail logs
- **Security Monitoring**: Configure CloudWatch alarms for security events
- **Vulnerability Management**: Regularly scan for and remediate vulnerabilities
- **Compliance Monitoring**: Continuously validate compliance with security standards
- **Anomaly Detection**: Detect and alert on unusual activity patterns

Regular security assessments are conducted to ensure ongoing compliance with these standards.

## Backlog

## Glossary

- ACU: Aurora Capacity Unit used by Aurora Serverless v2 to represent compute capacity
- CDK: AWS Cloud Development Kit for defining cloud infrastructure in code
- CI/CD: Continuous Integration / Continuous Delivery pipeline automating build, test, deploy
- NAG: cdk-nag AwsSolutions rules that enforce AWS best practices
- PI: Performance Insights (RDS feature for performance analysis)
- SSM: AWS Systems Manager Parameter Store for configuration parameters
- VPC: Virtual Private Cloud network environment in AWS

## References

- Pipeline stack: cdk/stacks/pipeline_stack.py

- Database stack: cdk/stacks/postgres_serverless_database_stack.py

- S3 stack: cdk/stacks/s3_stack.py

- Shared resources stage: cdk/stages/shared_resources_stage.py

- Database stage: cdk/stages/database_stage.py

- Stages orchestration: cdk/stages/logic/stages.py

- Imported resources construct: cdk/constructs/imported_resources_construct.py

- Configuration schema: cdk/schemas/configuration_vars.py

- Environment configs: cdk/config/{dev,acc,prod}/config.yaml

- Global CI/CD config: cdk/config/config-ci-cd.yaml

- Diagram script: documentation/postgres_serverless_database_architecture.py

- Makefile commands: Makefile

- Python 3.13+

- AWS CDK

- Pytest for testing

- Pre-commit for code quality checks

## Git repositories

## Project structure

- cdk/ - Infrastructure as Code (IaC) definitions
- cdk/config/ - Environment-specific configuration files
- cdk/constructs/ - Custom CDK constructs
- cdk/schemas/ - Pydantic models for configuration validation
- cdk/stacks/ - CDK stack definitions
- cdk/stages/ - CDK pipeline stages
- tests/ - Unit and infrastructure tests
- documentation/ - Architecture documentation

# Backlog
