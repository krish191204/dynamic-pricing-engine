# Data

The page sample is a real extract from the UCI Online Retail data set.

Chen, Daqing; Sain, Sai Laing; Guo, Kun (2012). *Data mining for the online retail industry: A case study of RFM model-based customer segmentation using data mining.* Journal of Database Marketing & Customer Strategy Management. Dataset: Online Retail, UCI Machine Learning Repository, https://archive.ics.uci.edu/dataset/352/online+retail. Licence: CC BY 4.0.

`data/uci_85123A.csv` is every invoice line for StockCode `85123A` (WHITE HANGING HEART T-LIGHT HOLDER) plus twenty real lines for `71053` (WHITE METAL LANTERN) so cleaning has another product to drop. Dates run from 1 December 2010 to 9 December 2011. Cancelled invoices keep the leading `C`. Unit cost is not in the source file. The form uses 1.20 as a typed cost, stock 400, eight weeks until leftover stock is treated as a loss, market price 2.55 (a price that appears in the file), and a 15% sales fall if price rises 10%. Those last four numbers are operator inputs, not columns in UCI.
