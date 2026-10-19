"""Versioned journal watchlist; historical editions keep their original rows."""
GROUPS = (
 ('memory', '存储与内存', 'Memory'),
 ('storage', '存储设备及配套', 'Storage and components'),
 ('compute', '算力芯片与制造', 'Compute and manufacturing'),
 ('netpower', '互联与供电散热', 'Networking, power and cooling'),
 ('platform', '平台与应用', 'Platforms and applications'),
)
ADDITIONS = {
 'us': [('MU','美光','Micron'),('SNDK','Sandisk','Sandisk'),('WDC','西部数据','Western Digital'),('STX','希捷','Seagate'),('AVGO','博通','Broadcom'),('TSM','台积电ADR','TSMC ADR'),('ANET','Arista','Arista Networks'),('VRT','Vertiv','Vertiv')],
 'cn': [('688825','长鑫科技','CXMT'),('688008','澜起科技','Montage Technology'),('603986','兆易创新','GigaDevice'),('301308','江波龙','Longsys'),('688525','佰维存储','BIWIN')],
 'hk': [],
 'kr': [('000660','SK海力士','SK hynix'),('005930','三星电子','Samsung Electronics')],
}
GROUP_TICKERS = {
 'memory': ('MU','SNDK','000660','005930','688825'),
 'storage': ('WDC','STX','688008','603986','301308','688525'),
 'compute': ('AVGO','TSM','NVDA','AMD','INTC','688256','688041','00981'),
 'netpower': ('ANET','VRT'),
 'platform': ('MSFT','GOOGL','META','AMZN','002230','09888','09988','00700','00020'),
}
TICKER_GROUP = {ticker: group for group, tickers in GROUP_TICKERS.items() for ticker in tickers}

def securities(legacy, version):
    return {key: [*legacy.get(key, []), *extra] for key, extra in ADDITIONS.items()} if version == 3 else legacy
