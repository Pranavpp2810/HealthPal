import re
import pandas as pd
from sklearn import preprocessing
from sklearn.tree import DecisionTreeClassifier, _tree
import numpy as np
from sklearn.model_selection import train_test_split
import csv
import pyttsx3
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Read training and testing data
training = pd.read_csv('Training.csv')
testing = pd.read_csv('Testing.csv')
cols = training.columns[:-1]
x = training[cols]
y = training['prognosis']
y1 = y

# Group by prognosis and get the maximum value for each group
reduced_data = training.groupby(training['prognosis']).max()

# Map strings to numbers
le = preprocessing.LabelEncoder()
le.fit(y)
y = le.transform(y)

# Split the data into training and testing sets
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.33, random_state=42)
testx = testing[cols]
testy = testing['prognosis']
testy = le.transform(testy)

# Create a Decision Tree Classifier and fit the training data
clf = DecisionTreeClassifier()
clf.fit(x_train, y_train)

# Rest of the code remains unchanged
importances = clf.feature_importances_
indices = np.argsort(importances)[::-1]
features = cols

def read_text(nstr):
    engine = pyttsx3.init()
    engine.say(nstr)
    engine.runAndWait()
    engine.stop()

severityDictionary = dict()
description_list = dict()
precautionDictionary = dict()

symptoms_dict = {}

for index, symptom in enumerate(x):
    symptoms_dict[symptom] = index

def calc_condition(exp, days):
    sum = 0
    for item in exp:
        if item in severityDictionary:
            sum += severityDictionary[item]
    print("\nResult:")
    if (sum * days) / (len(exp) + 1) > 13:
        result = "You should take consultation from a doctor."
    else:
        result = "It might not be that bad, but you should take precautions."
    print(result)
    read_text(result)
def getDescription():
    global description_list
    with open('symptom_Description.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _description = {row[0]: row[1]}
            description_list.update(_description)

def getSeverityDict():
    global severityDictionary
    with open('symptom_severity.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        try:
            for row in csv_reader:
                _diction = {row[0]: int(row[1])}
                severityDictionary.update(_diction)
        except:
            pass

def getprecautionDict():
    global precautionDictionary
    with open('symptom_precaution.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            _prec = {row[0]: [row[1], row[2], row[3], row[4]]}
            precautionDictionary.update(_prec)

def getInfo():
    print("-----------------------------------HealthPal ChatBot-----------------------------------")
    print("\nYour Name? \t\t\t\t", end="->")
    name = input("")
    print("Hello, ", name)

def check_pattern(dis_list, inp):
    pred_list = []
    inp = inp.replace(' ', '_')
    patt = f"{inp}"
    regexp = re.compile(patt)
    pred_list = [item for item in dis_list if regexp.search(item)]
    if len(pred_list) > 0:
        return 1, pred_list
    else:
        return 0, []

def sec_predict(symptoms_exp):
    df = pd.read_csv('Training.csv')
    X = df.iloc[:, :-1]
    y = df['prognosis']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=20)
    rf_clf = DecisionTreeClassifier()
    rf_clf.fit(X_train, y_train)

    symptoms_dict = {symptom: index for index, symptom in enumerate(X)}
    input_vector = np.zeros(len(symptoms_dict))
    for item in symptoms_exp:
        input_vector[[symptoms_dict[item]]] = 1

    return rf_clf.predict([input_vector])

def print_disease(node):
    node = node[0]
    val = node.nonzero()
    disease = le.inverse_transform(val[0])
    return list(map(lambda x: x.strip(), list(disease)))

def tree_to_code(tree, feature_names):
    tree_ = tree.tree_
    feature_name = [
        feature_names[i] if i != _tree.TREE_UNDEFINED else "undefined!"
        for i in tree_.feature
    ]

    chk_dis = ",".join(feature_names).split(",")
    symptoms_present = []

    while True:
        print("\nEnter the symptom you are experiencing  \t\t", end="->")
        disease_input = input("")
        conf, cnf_dis = check_pattern(chk_dis, disease_input)
        if conf == 1:
            print("searches related to input: ")
            for num, it in enumerate(cnf_dis):
                print(num, ")", it)
            if num != 0:
                print(f"Select the one you meant (0 - {num}):  ", end="")
                conf_inp = int(input(""))
            else:
                conf_inp = 0

            disease_input = cnf_dis[conf_inp]
            break
        else:
            print("Enter a valid symptom.")

    while True:
        try:
            num_days = int(input("Okay. From how many days? : "))
            break
        except:
            print("Enter a valid input.")

    def recurse(node, depth):
        indent = "  " * depth
        if tree_.feature[node] != _tree.TREE_UNDEFINED:
            name = feature_name[node]
            threshold = tree_.threshold[node]

            if name == disease_input:
                val = 1
            else:
                val = 0
            if val <= threshold:
                recurse(tree_.children_left[node], depth + 1)
            else:
                symptoms_present.append(name)
                recurse(tree_.children_right[node], depth + 1)
        else:
            present_disease = print_disease(tree_.value[node])
            red_cols = reduced_data.columns
            symptoms_given = red_cols[reduced_data.loc[present_disease].values[0].nonzero()]
            print("\nAre you experiencing any:")
            symptoms_exp = []
            for syms in list(symptoms_given):
                inp = ""
                print(syms, "? : ", end='')
                while True:
                    inp = input("")
                    if inp.lower() == "yes" or inp.lower() == "no":
                        break
                    else:
                        print("Provide proper answers (yes/no): ", end="")
                if inp.lower() == "yes":
                    symptoms_exp.append(syms)

            second_prediction = sec_predict(symptoms_exp)
            calc_condition(symptoms_exp, num_days)
            if present_disease[0] == second_prediction[0]:
                result = f"\nYou may have {present_disease[0]}\n{description_list[present_disease[0]]}"
            else:
                result = f"\nYou may have {present_disease[0]} or {second_prediction[0]}\n"
                result += f"{description_list[present_disease[0]]}\n{description_list[second_prediction[0]]}"

            read_text(result)  # Ensure text-to-speech engine is initialized before reading
            print(result)

            precaution_list = precautionDictionary[present_disease[0]]
            print("\nTake the following measures:")
            for i, j in enumerate(precaution_list):
                print(i + 1, ")", j)
                read_text(j)
    
    recurse(0, 1)

getSeverityDict()
getDescription()
getprecautionDict()
getInfo()
tree_to_code(clf, cols)
warnings.resetwarnings()
print("----------------------------------------------------------------------------------------")
