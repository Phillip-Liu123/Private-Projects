import json
from datamodel import OrderDepth, TradingState, Order  # Provided by the simulation environment.
from typing import List

class Trader:
    def run(self, state: TradingState):
        """
        This function is the main entry point of the trading algorithm.
        It is called repeatedly by the simulation engine with updated market data.
        The function returns a dictionary mapping product names to lists of orders,
        along with a conversion request value and a persistent state string (traderData).
        """
        # Load persistent state (historical data, etc.) from previous iterations.
        try:
            trader_data = json.loads(state.traderData)
        except Exception:
            trader_data = {}

        # Dictionary to collect orders for each product.
        orders_to_send = {}

        # Iterate through each product's order depth in the market.
        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []  # List to store orders for the current product.
            
            # Calculate mid-price:
            # The mid-price is a rough estimate of a product's "fair value" and is computed as:
            # (Best Bid + Best Ask) / 2.
            # The best bid is the highest price among buy orders, and the best ask is the lowest price among sell orders.
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders.keys(), key=float)
                best_ask = min(order_depth.sell_orders.keys(), key=float)
                mid_price = (float(best_bid) + float(best_ask)) / 2
            elif order_depth.buy_orders:
                mid_price = float(max(order_depth.buy_orders.keys(), key=float))
            elif order_depth.sell_orders:
                mid_price = float(min(order_depth.sell_orders.keys(), key=float))
            else:
                # If there are no orders available, skip processing this product.
                continue

            # Maintain a price history for each product to compute statistical measures like SMA.
            if product not in trader_data:
                trader_data[product] = {"prices": []}
            trader_data[product]["prices"].append(mid_price)
            # Limit the history to the last 20 mid-prices to keep the SMA computation manageable.
            if len(trader_data[product]["prices"]) > 20:
                trader_data[product]["prices"] = trader_data[product]["prices"][-20:]
            
            # Compute the Simple Moving Average (SMA) as our estimate of the product's fair price.
            sma = sum(trader_data[product]["prices"]) / len(trader_data[product]["prices"])
            
            # Define a threshold (5% of the SMA) to determine when a price deviation is significant.
            threshold = 0.05 * sma
            acceptable_price = sma  # In this strategy, our fair price is taken to be the SMA.

            # ---- Trading Strategy based on Order Book and Price Deviations ----
            # The trading glossary explains:
            # - A bid order is a BUY order and an ask order (or offer) is a SELL order.
            # - Orders are matched when buy orders are priced higher than sell orders.
            #
            # Here we exploit a potential mean-reversion:
            # If the best available sell price (ask) is significantly below our fair price,
            # it indicates a buying opportunity because the asset is "cheap."
            if order_depth.sell_orders:
                best_sell_price = float(min(order_depth.sell_orders.keys(), key=float))
                best_sell_volume = order_depth.sell_orders[min(order_depth.sell_orders.keys(), key=float)]
                if best_sell_price < acceptable_price - threshold:
                    # A negative volume indicates a BUY order in this simulation context.
                    orders.append(Order(product, best_sell_price, -abs(best_sell_volume)))
            
            # Similarly, if the best available buy price (bid) is significantly above our fair price,
            # it indicates a selling opportunity because the asset is "expensive."
            if order_depth.buy_orders:
                best_buy_price = float(max(order_depth.buy_orders.keys(), key=float))
                best_buy_volume = order_depth.buy_orders[max(order_depth.buy_orders.keys(), key=float)]
                if best_buy_price > acceptable_price + threshold:
                    # A positive volume indicates a SELL order.
                    orders.append(Order(product, best_buy_price, abs(best_buy_volume)))
            
            # Append any orders we have created for the current product.
            orders_to_send[product] = orders

        # Update the persistent state (traderData) with the new price history.
        new_trader_data_str = json.dumps(trader_data)
        
        # Conversion request sample (used by simulation, can be adjusted as needed).
        conversions = 1
        
        # Submission identifier is essential for tracking your algorithm in the competition.
        submission_uuid = "59f81e67-f6c6-4254-b61e-39661eac6141"
        print("Submission UUID:", submission_uuid)

        # Return the orders, conversion request, and updated traderData.
        return orders_to_send, conversions, new_trader_data_str
