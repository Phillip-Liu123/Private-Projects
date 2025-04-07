import json
from datamodel import OrderDepth, TradingState, Order
from typing import List

class Trader:

    def run(self, state: TradingState):
        # Try to load previously saved state (e.g. historical prices) from traderData.
        try:
            trader_data = json.loads(state.traderData)
        except Exception:
            trader_data = {}

        orders_to_send = {}

        # Loop over all products in the market.
        for product, order_depth in state.order_depths.items():
            orders: List[Order] = []
            
            # Check if we have valid order book data to compute a mid-price.
            if order_depth.buy_orders and order_depth.sell_orders:
                best_bid = max(order_depth.buy_orders.keys(), key=float)
                best_ask = min(order_depth.sell_orders.keys(), key=float)
                mid_price = (float(best_bid) + float(best_ask)) / 2
            elif order_depth.buy_orders:
                mid_price = float(max(order_depth.buy_orders.keys(), key=float))
            elif order_depth.sell_orders:
                mid_price = float(min(order_depth.sell_orders.keys(), key=float))
            else:
                # No available orders means no trading opportunity.
                continue

            # Maintain a history of mid-prices per product.
            if product not in trader_data:
                trader_data[product] = {"prices": []}
            trader_data[product]["prices"].append(mid_price)
            # Limit history to the most recent 20 prices.
            if len(trader_data[product]["prices"]) > 20:
                trader_data[product]["prices"] = trader_data[product]["prices"][-20:]
            
            # Calculate a simple moving average as our fair price estimate.
            sma = sum(trader_data[product]["prices"]) / len(trader_data[product]["prices"])
            
            # Define a threshold; if current price deviates by more than 5% from the SMA, act.
            threshold = 0.05 * sma
            acceptable_price = sma

            # Trading logic:
            # - If the best ask (sell order price) is significantly below our acceptable price,
            #   then there is a buying opportunity.
            if order_depth.sell_orders:
                best_sell_price = float(min(order_depth.sell_orders.keys(), key=float))
                best_sell_volume = order_depth.sell_orders[min(order_depth.sell_orders.keys(), key=float)]
                if best_sell_price < acceptable_price - threshold:
                    # Place a buy order by sending a negative quantity.
                    orders.append(Order(product, best_sell_price, -abs(best_sell_volume)))
            
            # - If the best bid (buy order price) is significantly above our acceptable price,
            #   then there is a selling opportunity.
            if order_depth.buy_orders:
                best_buy_price = float(max(order_depth.buy_orders.keys(), key=float))
                best_buy_volume = order_depth.buy_orders[max(order_depth.buy_orders.keys(), key=float)]
                if best_buy_price > acceptable_price + threshold:
                    # Place a sell order by sending a positive quantity.
                    orders.append(Order(product, best_buy_price, abs(best_buy_volume)))
            
            orders_to_send[product] = orders

        # Convert updated trader_data back to a string for persistence.
        new_trader_data_str = json.dumps(trader_data)
        
        # Sample conversion request (can be adjusted as needed).
        conversions = 1
        
        # Submission identifier provided for tracking purposes.
        submission_uuid = "59f81e67-f6c6-4254-b61e-39661eac6141"
        print("Submission UUID:", submission_uuid)

        return orders_to_send, conversions, new_trader_data_str

