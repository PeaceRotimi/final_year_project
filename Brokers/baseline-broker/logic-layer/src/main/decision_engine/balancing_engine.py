class BalancingEngine:
    def __init__(self):
        # the maximum imbalance before cutting power

        self.imbalance_threshold = -50.0

    def manage_imbalance(self,controllable_tariffs, esti_imbalance, total_controllable_capacity=100.0):

        commands = []

        if esti_imbalance < self.imbalance_threshold:

            shortfall = abs(esti_imbalance)
            curtailment_ratio = shortfall/total_controllable_capacity

            curtailment_ratio = min(1.0, curtailment_ratio)

            for tarrif_id in controllable_tariffs:
                commands.append({
                    "action": "balancing_order",
                    "tariffId": tarrif_id,
                    "curtailment": curtailment_ratio
                })
        return commands
