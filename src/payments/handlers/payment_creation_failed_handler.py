"""
Handler: Payment Creation Failed
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from db import get_sqlalchemy_session
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer
from stocks.commands.write_stock import check_in_items_to_stock, update_stock_redis


class PaymentCreationFailedHandler(EventHandler):
    """Handles PaymentCreationFailed events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "PaymentCreationFailed"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        # TODO: Consultez le diagramme de machine à états pour savoir quelle opération effectuer dans cette méthode. 
        # Conseil : inspirez-vous de OrderCreatedHandler ;)
        
        session = get_sqlalchemy_session()
        order_items = event_data.get("order_items", [])

        try:
            # Si réussi, déclenchez StockIncreased
            if not order_items:
                raise ValueError("OrderItem Manquants")
            
            check_in_items_to_stock(session, order_items)

            session.commit()
            update_stock_redis(order_items, "+")

            event_data['event'] = "StockIncreased"
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)
        except Exception as e:
            # TODO: Si l'operation a échoué, continuez la compensation des étapes précedentes.
            session.rollback()
            event_data['error'] = str(e)
            self.logger.error(f"Stock n'a pu etre integer : {e}")
        finally:
            session.close()
            event_data["event"] = "StockIncreased"
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)
