class ExchangeAPI:
    """
    A generic interface for interacting with different exchange APIs.
    """

    async def fetch_market_data(self, asset, endpoint):
        '''Fetches market data from the exchange API.'''
        raise NotImplementedError

    async def execute_trade(self, asset, side, quantity, price):
        '''Executes a trade on the exchange.'''
        raise NotImplementedError

    async def get_account_balance(self, asset):
        '''Gets the account balance for the specified asset.'''
        raise NotImplementedError

    async def fetch_order_book(self, asset, limit=100):
        '''Fetches the order book for the specified asset.'''
        raise NotImplementedError