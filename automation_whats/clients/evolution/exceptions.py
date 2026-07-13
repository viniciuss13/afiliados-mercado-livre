class EvolutionAPIError(Exception):
    """Exceção base para erros gerados pelo client da Evolution API."""


class EvolutionConfigError(EvolutionAPIError):
    """Erro de configuração da Evolution API.

    Essa exceção é usada quando variáveis obrigatórias estão ausentes ou quando
    algum valor de configuração não atende às validações do projeto.
    """


class EvolutionResponseError(EvolutionAPIError):
    """Erro de resposta da Evolution API.

    Essa exceção é usada quando a API retorna status HTTP de erro ou quando a
    resposta não pode ser interpretada como JSON válido.
    """
