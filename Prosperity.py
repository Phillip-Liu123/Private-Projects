import json
from datamodel import OrderDepth, TradingState, Order  # These classes are provided by the simulation environment.
from typing import List

class Trader:
    def run(self, state: TradingState):
        """
        Main function that is repeatedly called by the trading simulation.
        It receives a TradingState object which contains all relevant market data,
        including current orders, recent trades, and a string for persisting state.
        """
        # Attempt to load the persistent trader data (e.g., historical mid-prices) from the state.
        # This allows the algorithm to "remember" previous iterations.
        try:
            trader_data = json.loads(state.traderData)
        except Exception:
            # If traderData is empty or invalid, initialize with an empty dictionary.
            trader_data = {}

        # This dictionary will hold the orders we decide to send for each product.
        orders_to_send = {}

        # Loop over each product in the current order depths provided by the simulation.
        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []  # List to collect orders for the current product.
            
            # Check if both buy and sell orders exist to calculate a fair mid-price.
            if order_depth.buy_orders and order_depth.sell_orders:
                # The best bid is the highest price someone is willing to buy.
                best_bid = max(order_depth.buy_orders.keys(), key=float)
                # The best ask is the lowest price someone is willing to sell.
                best_ask = min(order_depth.sell_orders.keys(), key=float)
                # Calculate the mid-price as the average of the best bid and best ask.
                mid_price = (float(best_bid) + float(best_ask)) / 2
            elif order_depth.buy_orders:
                # If there are only buy orders, use the best bid as a fallback mid-price.
                mid_price = float(max(order_depth.buy_orders.keys(), key=float))
            elif order_depth.sell_orders:
                # If there are only sell orders, use the best ask as a fallback mid-price.
                mid_price = float(min(order_depth.sell_orders.keys(), key=float))
            else:
                # If there are no orders available, skip trading for this product.
                continue

            # Initialize the history for this product if not already present.
            if product not in trader_data:
                trader_data[product] = {"prices": []}
            # Append the current mid-price to the historical list.
            trader_data[product]["prices"].append(mid_price)
            # To avoid unbounded growth of the history, limit it to the 20 most recent mid-prices.
            if len(trader_data[product]["prices"]) > 20:
                trader_data[product]["prices"] = trader_data[product]["prices"][-20:]
            
            # Calculate the simple moving average (SMA) of the stored mid-prices.
            sma = sum(trader_data[product]["prices"]) / len(trader_data[product]["prices"])
            
            # Define a threshold (5% of the SMA) to identify significant deviations.
            threshold = 0.05 * sma
            # Use the SMA as our acceptable or fair price for this product.
            acceptable_price = sma

            # --- Trading Signal Generation ---
            # Check if there's an opportunity to buy:
            # If the best sell price (ask) is significantly below our acceptable price, then it's a buying signal.
            if order_depth.sell_orders:
                best_sell_price = float(min(order_depth.sell_orders.keys(), key=float))
                best_sell_volume = order_depth.sell_orders[min(order_depth.sell_orders.keys(), key=float)]
                # Compare best sell price with the acceptable price, taking the threshold into account.
                if best_sell_price < acceptable_price - threshold:
                    # Create a buy order.
                    # Negative volume indicates a buy order in this simulation.
                    orders.append(Order(product, best_sell_price, -abs(best_sell_volume)))
            
            # Check if there's an opportunity to sell:
            # If the best buy price (bid) is significantly above our acceptable price, then it's a selling signal.
            if order_depth.buy_orders:
                best_buy_price = float(max(order_depth.buy_orders.keys(), key=float))
                best_buy_volume = order_depth.buy_orders[max(order_depth.buy_orders.keys(), key=float)]
                # Compare best buy price with the acceptable price, taking the threshold into account.
                if best_buy_price > acceptable_price + threshold:
                    # Create a sell order.
                    # Positive volume indicates a sell order in this simulation.
                    orders.append(Order(product, best_buy_price, abs(best_buy_volume)))
            
            # Add the orders for the current product to the final orders dictionary.
            orders_to_send[product] = orders

        # Convert the updated trader_data dictionary back to a JSON string for persistence.
        # This string will be available in the next iteration via state.traderData.
        new_trader_data_str = json.dumps(trader_data)
        
        # The simulation might allow conversion requests; we set this as a sample value.
        conversions = 1
        
        # Submission identifier is used for tracking in the trading competition.
        submission_uuid = "59f81e67-f6c6-4254-b61e-39661eac6141"
        print("Submission UUID:", submission_uuid)

        # Return the orders to send, the conversion request value, and the persistent state string.
        return orders_to_send, conversions, new_trader_data_str
