# Conversor Analítico - Enterprise Edition

Sistema de alto desempenho para conversão de arquivos CSV para formatos otimizados de Big Data, construído seguindo os princípios de Clean Architecture e SOLID.

## Visão Geral

Este projeto foi reestruturado para atender a padrões corporativos de escalabilidade, manutenibilidade e segurança. Ele permite a conversão de grandes volumes de dados CSV para formatos como Parquet, Feather, ORC e HDF5, com suporte a processamento em chunks para otimização de memória RAM.

## Arquitetura

O projeto segue a Clean Architecture Clássica, garantindo baixo acoplamento e alta coesão:

```mermaid
graph TD
    subgraph Presentation ["Presentation Layer (GUI)"]
        UI[CustomTkinter UI]
        Events[Event Emitter]
    end

    subgraph Application ["Application Layer (Use Cases)"]
        Validate[ValidateFilesUseCase]
        Convert[ConvertFilesUseCase]
        Ports[Interfaces / Ports]
    end

    subgraph Domain ["Domain Layer (Core)"]
        Entities[FormatMetadata]
        Bus[Business Rules]
    end

    subgraph Infrastructure ["Infrastructure Layer (Adapters)"]
        FS[LocalFileSystem]
        Reader[PandasCsvReader]
        Saver[PandasFileSaver]
        Detect[DetectorCSV]
    end

    UI --> Events
    Events --> Validate
    Events --> Convert
    
    Validate --> Ports
    Convert --> Ports
    
    Ports --> Entities
    Convert --> Entities
    
    FS -.->|Implements| Ports
    Reader -.->|Implements| Ports
    Saver -.->|Implements| Ports
    Detect -.->|Implements| Ports
    
    %% Setup Dependency Inversion Rule
    style Domain fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    style Application fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style Infrastructure fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style Presentation fill:#fce4ec,stroke:#880e4f,stroke-width:2px
```

- **Domain**: Regras de negócio essenciais e entidades independentes de frameworks.
- **Application**: Casos de uso que orquestram a lógica da aplicação e interfaces (portas).
- **Infrastructure**: Implementações técnicas (adaptadores) para acesso a arquivos, persistência e detecção de dados.
- **Presentation**: Interface gráfica (GUI) construída com CustomTkinter, utilizando mensageria assíncrona para operações thread-safe.

## Tecnologias

- Python 3.10+
- Pandas (Processamento de dados)
- PyArrow (Mecanismo de Big Data)
- CustomTkinter (Interface Moderna)
- Ruff/Mypy/Black (Qualidade de Código)

## Instalação

1. Certifique-se de ter o Python instalado.
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Execução

Inicie a aplicação através do ponto de entrada principal:
```bash
python main.py
```

## Qualidade de Código

O projeto utiliza ferramentas modernas para garantir a integridade do código:
- **Linting**: Ruff
- **Type Checking**: Mypy
- **Formatting**: Black

As configurações estão centralizadas no arquivo `pyproject.toml`.
