"""Módulo que contém as entidades principais do domínio."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Usuario:
    """
    Representa um usuário no sistema.
    
    Esta entidade encapsula as propriedades e comportamentos associados
    a um usuário, seguindo os princípios de domínio rico.
    
    Attributes:
        id: Identificador único do usuário.
        nome: Nome completo do usuário.
        email: Endereço de email do usuário.
        data_criacao: Data em que o usuário foi criado.
        ultimo_acesso: Data do último acesso do usuário ao sistema.
        ativo: Indica se o usuário está ativo no sistema.
    """
    
    id: int
    nome: str
    email: str
    data_criacao: datetime
    ultimo_acesso: Optional[datetime] = None
    ativo: bool = True
    
    def desativar(self) -> None:
        """
        Desativa o usuário no sistema.
        
        Este método muda o estado do usuário para inativo, impedindo
        que ele faça login ou execute operações no sistema.
        """
        self.ativo = False
    
    def registrar_acesso(self) -> None:
        """
        Registra um novo acesso do usuário ao sistema.
        
        Atualiza o timestamp do último acesso para o momento atual.
        """
        self.ultimo_acesso = datetime.now()
    
    def dias_desde_ultimo_acesso(self) -> Optional[int]:
        """
        Calcula quantos dias se passaram desde o último acesso do usuário.
        
        Returns:
            int: Número de dias desde o último acesso, ou None se nunca acessou.
        """
        if not self.ultimo_acesso:
            return None
            
        dias = (datetime.now() - self.ultimo_acesso).days
        return dias


@dataclass
class Projeto:
    """
    Representa um projeto no sistema.
    
    Um projeto é uma unidade organizacional que contém tarefas
    e pode ter vários usuários associados a ele.
    
    Attributes:
        id: Identificador único do projeto.
        nome: Nome do projeto.
        descricao: Descrição detalhada do projeto.
        data_criacao: Data em que o projeto foi criado.
        responsavel_id: ID do usuário responsável pelo projeto.
        membros: Lista de IDs dos usuários que são membros do projeto.
    """
    
    id: int
    nome: str
    descricao: str
    data_criacao: datetime
    responsavel_id: int
    membros: List[int] = None
    
    def __post_init__(self):
        """Inicializa membros como lista vazia se não fornecido."""
        if self.membros is None:
            self.membros = []
            
        # Garantir que o responsável está na lista de membros
        if self.responsavel_id not in self.membros:
            self.membros.append(self.responsavel_id)
    
    def adicionar_membro(self, usuario_id: int) -> None:
        """
        Adiciona um usuário como membro do projeto.
        
        Args:
            usuario_id: ID do usuário a ser adicionado ao projeto.
        """
        if usuario_id not in self.membros:
            self.membros.append(usuario_id)
    
    def remover_membro(self, usuario_id: int) -> bool:
        """
        Remove um usuário da lista de membros do projeto.
        
        Args:
            usuario_id: ID do usuário a ser removido.
            
        Returns:
            bool: True se o usuário foi removido, False se não era membro
                 ou se é o responsável pelo projeto.
        """
        if usuario_id == self.responsavel_id:
            return False  # Não pode remover o responsável
            
        if usuario_id in self.membros:
            self.membros.remove(usuario_id)
            return True
            
        return False
