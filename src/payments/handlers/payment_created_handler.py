"""
Handler: Payment Created
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
from typing import Dict, Any
import config
from event_management.base_handler import EventHandler
from orders.commands.order_event_producer import OrderEventProducer
from orders.commands.write_order import add_order_to_redis, modify_order

class PaymentCreatedHandler(EventHandler):
    """Handles PaymentCreated events"""
    
    def __init__(self):
        self.order_producer = OrderEventProducer()
        super().__init__()
    
    def get_event_type(self) -> str:
        """Get event type name"""
        return "PaymentCreated"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """Execute every time the event is published"""
        # TODO: Consultez le diagramme de machine à états pour savoir quelle opération effectuer dans cette méthode. Mettez votre commande à jour avec le nouveau payment_id.
        # N'oubliez pas d'enregistrer le payment_link dans votre commande
        order_id = event_data.get("order_id")
        payment_id = event_data.get("payment_id")
        user_id = event_data.get("user_id")
        total_amount = event_data.get("total_amount")
        order_items = event_data.get("order_items", [])

        try:
            if order_id is None or payment_id is None:
                raise ValueError("Il manque des données")

            payment_link = (
                event_data.get("payment_link")
                or f"http://api-gateway:8080/payments-api/payments/process/{payment_id}" #Prendre le end point directemen 
            )

            update_succeeded = modify_order(order_id, True, payment_id)
            if not update_succeeded :
                raise Exception("Update des donnees non reussi")
            
            if user_id is not None and total_amount is not None:
                add_order_to_redis(order_id, user_id, total_amount, order_items or [], payment_link)

            event_data["payment_link"] = payment_link

            # Si l'operation a réussi, déclenchez SagaCompleted.
            event_data['event'] = "SagaCompleted"
            self.logger.debug(f"payment_link={event_data['payment_link']}")
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)

        except Exception as e:
            # TODO: Si l'operation a échoué, déclenchez l'événement adéquat selon le diagramme.
            event_data['error'] = str(e)
            event_data["error"] = str(e)
            OrderEventProducer().get_instance().send(config.KAFKA_TOPIC, value=event_data)

