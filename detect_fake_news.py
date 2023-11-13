# -*- coding: utf-8 -*-
"""main test.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/github/Systematicos/Model-dectation-fake-news/blob/v4/notebooks/main%20test.ipynb
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import os
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
import re
import string
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay, classification_report, accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
from sklearn.model_selection import train_test_split

import pickle
import tensorflow as tf
from tensorflow.keras.models import load_model, Model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Input, Embedding, GRU, LSTM, SimpleRNN, Conv1D, Dense, Dropout, Attention, Bidirectional
from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.utils import plot_model

import nltk
nltk.download('stopwords')
log_dir = "logs/"  # Especifique o diretório onde os logs serão armazenados
tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)

df = pd.read_csv('data/fakeBr.csv')
df = df.drop(columns=['index'])
df.isnull().any()

stop_words = set(stopwords.words('portuguese'))

def remover_stop_words(news):
    palavras = news.split()
    palavras_sem_stop = [palavra for palavra in palavras if palavra.lower() not in stop_words]
    return ' '.join(palavras_sem_stop)

def review_cleaning(text):

    text = str(text).lower()
    text = re.sub('\[.*?\]', '', text)
    text = re.sub('https?://\S+|www\.\S+', '', text)
    text = re.sub('<.*?>+', '', text)
    text = re.sub('[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub('\n', '', text)
    text = re.sub('\w*\d\w*', '', text)
    return text

df["preprocessed_news"] = df["preprocessed_news"].apply(remover_stop_words)
df['label'] = df.apply(lambda row: 0 if row.label == 'fake' else 1, axis=1)
X = df.drop(['label'], axis = 1)
Y = df['label']

X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size = 0.3, stratify=Y)
X_train = X_train['preprocessed_news'].apply(lambda x: x.lower())
X_test = X_test['preprocessed_news'].apply(lambda x: x.lower())

#variaveis dos modelos
maxlen=256
num_words = 8000
batch_size = 128
epochs = 20
validation_fraction = 0.2
output_dim = 64



early_stopping = EarlyStopping(monitor='val_loss', patience=3)

train_tokenizer = tf.keras.preprocessing.text.Tokenizer(oov_token='<OOV>',num_words=num_words)
train_tokenizer.fit_on_texts(X_train.values)
train_word_index = train_tokenizer.word_index
train_sequences = train_tokenizer.texts_to_sequences(X_train)

text_tokenizer = tf.keras.preprocessing.text.Tokenizer(oov_token='<OOV>',num_words=num_words)
text_tokenizer.fit_on_texts(X_test.values)
text_word_index = text_tokenizer.word_index
text_sequences = text_tokenizer.texts_to_sequences(X_test)

vocab_length = len(train_word_index) + 1

train_padded_seqeunces = tf.keras.preprocessing.sequence.pad_sequences(train_sequences, maxlen=maxlen)
test_padded_seqeunces = tf.keras.preprocessing.sequence.pad_sequences(text_sequences, maxlen=maxlen)

train_padded_seqeunces = train_padded_seqeunces[:, :, tf.newaxis]
test_padded_seqeunces = test_padded_seqeunces[:, :, tf.newaxis]

x_train_padded_seqeunces = train_padded_seqeunces[:, :, tf.newaxis]
x_test_padded_seqeunces = test_padded_seqeunces[:, :, tf.newaxis]

vectorizer = CountVectorizer(max_features=num_words)
vectorizer.fit(X_train)
X_train = vectorizer.transform(X_train).toarray()

vectorizer = CountVectorizer(max_features=num_words)
vectorizer.fit(X_test)
X_test = vectorizer.transform(X_test).toarray()

with open('models/MLPClassifierWithGridSearchCV.pkl', 'rb') as arquivo:
    clf = pickle.load(arquivo)

modelLSTM = load_model('models/modelLSTM.keras')
modelHAN = load_model('models/modelHAN.keras')

"""#### MLP"""

print("Inicio do Teste")
y_test_pred = clf.predict(X_test)
y_test_pred = (y_test_pred > 0.70)
mlp_acc = round(accuracy_score(y_test, y_test_pred)* 100, 2)

cm = confusion_matrix(y_test, y_test_pred)

print("=" * 20)
print("Matriz de confusão")
cm_percentage = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100

disp = ConfusionMatrixDisplay(confusion_matrix=cm_percentage, display_labels=['Falsa','Verdadeira'])

disp.plot( values_format='.0f')
disp.ax_.set(xlabel='Previsão', ylabel='Verdade')
matriz_directory = 'matriz'
if not os.path.exists(matriz_directory):
    os.makedirs(matriz_directory)
plt.savefig('matriz/confusion_matrix_MLP%.png')
plt.show()
print("Fim do Teste")

"""#### RNN (LSTM bidirecionais)"""

print("Inicio do Teste")

y_test_pred = modelLSTM.predict(test_padded_seqeunces)
y_test_pred = (y_test_pred > 0.70)
lstm_acc = round(accuracy_score(y_test, y_test_pred) * 100, 2)

cm = confusion_matrix(y_test, y_test_pred)
cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100
print(classification_report(y_test, y_test_pred))

print("Matriz de confusão")
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Falsa','Verdadeira'], )
disp.plot(values_format='.0f')
disp.ax_.set(xlabel='Previsão', ylabel='Verdade')
plt.savefig('matriz/confusion_matrix_LSTM%.png')
plt.show()

print("Fim dos testes")

print("=" * 30)

"""#### RNN (HAN)"""

print("Inicio do Teste")
y_test_pred = modelHAN.predict(test_padded_seqeunces)
y_test_pred = (y_test_pred > 0.60)
han_acc = round(accuracy_score(y_test, y_test_pred) * 100, 2)
print(classification_report(y_test, y_test_pred))

cm = confusion_matrix(y_test, y_test_pred)
cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis] * 100

print("Matriz de confusão")
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Falsa','Verdadeira'], )
disp.plot(values_format='.0f')
disp.ax_.set(xlabel='Previsão', ylabel='Verdade')

plt.savefig('matriz/confusion_matrix_HAN%.png')
plt.show()

print("Fim dos testes")

print("=" * 30)

model = pd.DataFrame({
    'Model': [
        'MLP',
        'RNN LSTM(BI)',
        'HAN'
    ],
    'Test Accuracy': [

        mlp_acc ,lstm_acc,han_acc
    ]
})

train = model.sort_values('Test Accuracy',ascending=False)
print(train)