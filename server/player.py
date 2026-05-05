"""
Player management for the game.
Handles player state, hand management, and player-related operations.
"""

from typing import List, Optional
from shared.data_structures import Card, Player
from shared.enums import PlayerState


class PlayerManager:
    """
    Manages all players in the game room.
    Handles player state, hands, scores, and turn management.
    """
    
    def __init__(self):
        """Initialize the player manager."""
        self._players: dict[int, Player] = {}  # player_id -> Player

    def add_player(self, player_id: int, name: str, is_host: bool = False) -> Player:
        """
        Add a new player to the game.
        
        Args:
            player_id: Unique player ID
            name: Player's display name
            is_host: Whether this player is the host
            
        Returns:
            Player object
        """
        player = Player(
            player_id=player_id,
            name=name,
            is_host=is_host,
            is_connected=True,
            state=PlayerState.IDLE
        )
        self._players[player_id] = player
        return player

    def remove_player(self, player_id: int):
        """
        Remove a player from the game.
        
        Args:
            player_id: ID of player to remove
        """
        self._players.pop(player_id, None)

    def get_player(self, player_id: int) -> Optional[Player]:
        """
        Get a player by ID.
        
        Args:
            player_id: Player ID
            
        Returns:
            Player object or None
        """
        return self._players.get(player_id)

    def get_all_players(self) -> List[Player]:
        """Get all active players."""
        return list(self._players.values())

    def set_player_state(self, player_id: int, state: PlayerState):
        """
        Set a player's state.
        
        Args:
            player_id: Player ID
            state: New PlayerState
        """
        player = self.get_player(player_id)
        if player:
            player.state = state

    def add_card_to_hand(self, player_id: int, card: Card):
        """
        Add a card to a player's hand.
        
        Args:
            player_id: Player ID
            card: Card to add
        """
        player = self.get_player(player_id)
        if player is not None:
            player.hand.append(card)

    def add_cards_to_hand(self, player_id: int, cards: List[Card]):
        """
        Add multiple cards to a player's hand.
        
        Args:
            player_id: Player ID
            cards: List of cards to add
        """
        player = self.get_player(player_id)
        if player is not None:
            player.hand.extend(cards)

    def remove_card_from_hand(self, player_id: int, card_index: int) -> Optional[Card]:
        """
        Remove a card from a player's hand by index.
        
        Args:
            player_id: Player ID
            card_index: Index of card in hand
            
        Returns:
            Removed card or None if invalid index
        """
        player = self.get_player(player_id)
        if player is None:
            return None
        if card_index < 0 or card_index >= len(player.hand):
            return None
        return player.hand.pop(card_index)

    def get_player_hand(self, player_id: int) -> List[Card]:
        """
        Get a player's hand.
        
        Args:
            player_id: Player ID
            
        Returns:
            List of Card objects
        """
        player = self.get_player(player_id)
        if player is None:
            return []
        return player.hand

    def get_player_hand_size(self, player_id: int) -> int:
        """Get the number of cards in a player's hand."""
        return len(self.get_player_hand(player_id))

    def update_player_score(self, player_id: int, points: int):
        """
        Add points to a player's score.
        
        Args:
            player_id: Player ID
            points: Points to add
        """
        player = self.get_player(player_id)
        if player is not None:
            player.score += points

    def clear_all_hands(self):
        """Clear all players' hands (used for game reset)."""
        for player in self._players.values():
            player.hand = []
