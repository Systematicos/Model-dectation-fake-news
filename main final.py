# -*- coding: utf-8 -*-
"""main com final e teste junto.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11oxlp5HRNJUH33kjEdqGGgG786G0eYTt
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
import re
import string
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay, classification_report, accuracy_score
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression, PassiveAggressiveClassifier
import pickle
import tensorflow as tf
from tensorflow.keras.models import load_model

import nltk
nltk.download('stopwords')

df = pd.read_csv('data/train.csv')
df = df.drop(columns=['Unnamed: 0'])

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
df["preprocessed_news"] = df["preprocessed_news"].apply(review_cleaning)

df['label'] = df.apply(lambda row: 0 if row.label == 'fake' else 1, axis=1)

X_train = df.drop(['label'], axis = 1)
Y_train = df['label']

X_train = X_train['preprocessed_news'].apply(lambda x: x.lower())

train_tokenizer = tf.keras.preprocessing.text.Tokenizer(oov_token='<OOV>')
train_tokenizer.fit_on_texts(X_train.values)
train_word_index = train_tokenizer.word_index
train_sequences = train_tokenizer.texts_to_sequences(X_train)
vocab_length = len(train_word_index) + 1
maxlen=256
train_padded_seqeunces = tf.keras.preprocessing.sequence.pad_sequences(train_sequences, padding='post', maxlen=maxlen, truncating='post')


vectorizer = CountVectorizer(max_features=10000)
vectorizer.fit(X_train)
X_train = vectorizer.transform(X_train).toarray()

with open('models/v2/rnn_tokenizer.pkl', 'wb') as arquivo:
    pickle.dump(train_tokenizer, arquivo)
with open('models/v2/count_vectorizer.pkl', 'wb') as arquivo:
    pickle.dump(vectorizer, arquivo)

"""##### Logistic Regression

"""

lr_classifier = LogisticRegression()
lr_classifier.fit(X_train,Y_train)
lr_classifier_train = round(lr_classifier.score(X_train, Y_train) * 100, 2)

with open('models/v2/logisticRegression.pkl', 'wb') as arquivo:
    pickle.dump(lr_classifier, arquivo)

"""##### Multilayer perceptron (MLP)"""

mlp = MLPClassifier(random_state=1)
mlp.fit(X_train,Y_train)
mlp_train = round(mlp.score(X_train, Y_train) * 100, 2)

with open('models/v2/MLPClassifier.pkl', 'wb') as arquivo:
    pickle.dump(mlp, arquivo)

"""##### Multilayer perceptron (MLP) Com GridSearchCV"""

parameters = {'solver': ['sgd', 'adam'],
              'hidden_layer_sizes':(10,5,2),
              'random_state':[2],
              'activation': ['tanh', 'relu'],
              'max_iter': [100]
              }

clf = GridSearchCV(MLPClassifier(), parameters, cv=2)
clf.fit(X_train,Y_train)
mlpG_train = round(clf.score(X_train, Y_train) * 100, 2)


with open('models/v2/MLPClassifierWithGridSearchCV.pkl', 'wb') as arquivo:
    pickle.dump(clf, arquivo)

"""#### Decision Tree"""

decisionTree = DecisionTreeClassifier()
decisionTree.fit(X_train,Y_train)
decisionTree_train = round(clf.score(X_train, Y_train) * 100, 2)

with open('models/v2/decisionTree.pkl', 'wb') as arquivo:
    pickle.dump(decisionTree, arquivo)

"""#### Passive Aggressive"""

passive = PassiveAggressiveClassifier(C = 0.5, random_state = 5)
passive.fit(X_train,Y_train)
passive_train = round(passive.score(X_train, Y_train) * 100, 2)

with open('models/v2/PassiveAggressiveClassifier.pkl', 'wb') as arquivo:
    pickle.dump(passive, arquivo)

"""RNN"""

output_dim = 64
epochs = 60
batch_size = 32
tf.keras.backend.clear_session()

modelSimpleRNN = tf.keras.models.Sequential()
modelSimpleRNN.add(tf.keras.layers.Embedding(vocab_length, output_dim, input_length=maxlen))
modelSimpleRNN.add(tf.keras.layers.GRU(60, activation='tanh', return_sequences=True))
modelSimpleRNN.add(tf.keras.layers.Conv1D(30, 3, activation='relu'))
modelSimpleRNN.add(tf.keras.layers.LSTM(30, return_sequences=True))
modelSimpleRNN.add(tf.keras.layers.SimpleRNN(3, activation='tanh'))
modelSimpleRNN.add(tf.keras.layers.Dropout(0.25))
modelSimpleRNN.add(tf.keras.layers.Dense(24, activation='relu'))
modelSimpleRNN.add(tf.keras.layers.Dense(units = 1, activation='sigmoid'))
modelSimpleRNN.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

historySimpleRNN = modelSimpleRNN.fit(train_padded_seqeunces, Y_train, epochs=epochs, batch_size=batch_size, validation_split=0.1)
rnn_train = round(historySimpleRNN.history['accuracy'][-1] * 100, 2)
modelSimpleRNN.save('models/v2/modelo_rnn.keras')

"""## Test"""

with open('models/v2/rnn_tokenizer.pkl', 'rb') as arquivo:
    tokenizer = pickle.load(arquivo)
with open('models/v2/count_vectorizer.pkl', 'rb') as arquivo:
    vectorizer_test = pickle.load(arquivo)

maxlen=256

df_test = pd.read_csv('data/test.csv')
df_test = df_test.drop(columns=['Unnamed: 0'])

df_test["preprocessed_news"] = df_test["preprocessed_news"].apply(remover_stop_words)
df_test["preprocessed_news"] = df_test["preprocessed_news"].apply(review_cleaning)

df_test['label'] = df_test.apply(lambda row: 0 if row.label == 'fake' else 1, axis=1)

X_test = df_test.drop(['label'], axis = 1)
Y_test = df_test['label']

X_test = X_test['preprocessed_news'].apply(lambda x: x.lower())

test_sequences = train_tokenizer.texts_to_sequences(X_test)
test_padded_seqeunces = tf.keras.preprocessing.sequence.pad_sequences(test_sequences, padding='post', maxlen=maxlen, truncating='post')

X_test = vectorizer_test.transform(X_test).toarray()

with open('models/v2/logisticRegression.pkl', 'rb') as arquivo:
    lr_classifier = pickle.load(arquivo)
with open('models/v2/MLPClassifier.pkl', 'rb') as arquivo:
    mlp = pickle.load(arquivo)
with open('models/v2/MLPClassifierWithGridSearchCV.pkl', 'rb') as arquivo:
    mlpG = pickle.load(arquivo)
with open('models/v2/decisionTree.pkl', 'rb') as arquivo:
    decisionTree = pickle.load(arquivo)
with open('models/v2/PassiveAggressiveClassifier.pkl', 'rb') as arquivo:
    passive = pickle.load(arquivo)

rnn = load_model('models/v2/modelo_rnn.keras')

"""##### Logistic Regression

"""

y_test_pred = lr_classifier.predict(X_test)
y_test_pred = (y_test_pred > 0.75)
lr_classifier_acc = round(accuracy_score(Y_test, y_test_pred) * 100, 2)
cm = confusion_matrix(Y_test, y_test_pred)
print(classification_report(Y_test, y_test_pred))

ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fake','True']).plot()

"""##### Multilayer perceptron (MLP)"""

y_test_pred = mlp.predict(X_test)
y_test_pred = (y_test_pred > 0.75)
mlp_acc = round(accuracy_score(Y_test, y_test_pred) * 100, 2)

cm = confusion_matrix(Y_test, y_test_pred)
print(classification_report(Y_test, y_test_pred))

ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fake','True']).plot()

"""##### Multilayer perceptron (MLP) Com GridSearchCV"""

y_test_pred = mlpG.predict(X_test)
y_test_pred = (y_test_pred > 0.75)
mlpG_acc = round(accuracy_score(Y_test, y_test_pred) * 100, 2)

cm = confusion_matrix(Y_test, y_test_pred)
print(classification_report(Y_test, y_test_pred))

ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fake','True']).plot()

"""#### Decision Tree"""

y_test_pred = decisionTree.predict(X_test)
y_test_pred = (y_test_pred > 0.75)
decisionTree_acc = round(accuracy_score(Y_test, y_test_pred) * 100, 2)

cm = confusion_matrix(Y_test, y_test_pred)
print(classification_report(Y_test, y_test_pred))

ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fake','True']).plot()

"""#### Passive Aggressive"""

x_test_pred = passive.predict(X_test)
y_test_pred = (y_test_pred > 0.75)
passive_acc = round(accuracy_score(Y_test, y_test_pred) * 100, 2)

cm = confusion_matrix(Y_test, y_test_pred)
print(classification_report(Y_test, y_test_pred))

ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fake','True']).plot()

"""#### RNN"""

y_test_pred = rnn.predict(test_padded_seqeunces)
y_test_pred = (y_test_pred > 0.70)
rnn_acc = round(accuracy_score(Y_test, y_test_pred) * 100, 2)

cm = confusion_matrix(Y_test, y_test_pred)
print(classification_report(Y_test, y_test_pred))

ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Fake','True']).plot()

"""### Comparando Modelos Diferentes"""

model = pd.DataFrame({
    'Model': [
        'Logistic Regression',
        'Decision Tree',
        'MLPClassifier',
        'MLPClassifier with grid',
        'PassiveAggressiveClassifier',
        'RNN'
    ],
    'Training Accuracy': [
        lr_classifier_train, decisionTree_train,
        mlp_train,mlpG_train, passive_train,rnn_train
    ],
    'Model Accuracy Score': [
        lr_classifier_acc, decisionTree_acc,
        mlp_acc, mlpG_acc, passive_acc,rnn_acc
    ]
})

model = model.sort_values('Model Accuracy Score',ascending=False)
print(model)