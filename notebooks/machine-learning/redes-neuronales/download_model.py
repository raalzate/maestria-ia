import fasttext.util
fasttext.util.download_model('es', if_exists='ignore')  # English
ft = fasttext.load_model('cc.es.300.vec')