"""
Handler: Stock Decreased
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer
from orders.commands.write_order import delete_order

class StockIncreasedHandler(EventHandler):
    """Handles StockIncrease events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "StockIncreased"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        order_id = event_data.get('order_id')
        event_data['event'] = "OrderCancelled"

        try:
            if order_id is None:
                raise ValueError("order_id manquant dans l'événement StockIncreased.")

            deleted = delete_order(order_id)
            if deleted == 0:
                raise ValueError(f"La commande {order_id} n'existe pas ou a déjà été supprimée.")

            self.logger.debug(f"Commande {order_id} annulée après réintégration du stock.")

        except Exception as e:
            # Même si l'annulation échoue, poursuivez la compensation avec les informations d'erreur.
            event_data['error'] = str(e)
            self.logger.error(f"Impossible d'annuler la commande {order_id}: {e}")
        finally:
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)




