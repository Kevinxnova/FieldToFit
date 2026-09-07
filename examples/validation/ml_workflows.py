"""Reproducible CPU learning/baseline examples using the library's bundled digits data."""
import json
import sys
from importlib.metadata import version
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression,SGDClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

case=sys.argv[1]
data=load_digits()
X_train,X_test,y_train,y_test=train_test_split(data.data,data.target,test_size=.25,random_state=42,stratify=data.target)
if case=='researcher-model-data':
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=42)); minimum=.90
elif case=='graduate-baseline':
    model=SVC(gamma=.001);minimum=.90
elif case=='graduate-budget':
    model=make_pipeline(StandardScaler(),SGDClassifier(random_state=42,max_iter=2000,tol=1e-4));minimum=.85
elif case=='student-minimal':
    model=DecisionTreeClassifier(max_depth=12,random_state=42);minimum=.75
elif case=='student-course':
    model=make_pipeline(StandardScaler(),LogisticRegression(max_iter=1000,random_state=42));minimum=.90
else: raise ValueError('Unknown reviewed case')
model.fit(X_train,y_train);predictions=model.predict(X_test);score=accuracy_score(y_test,predictions)
assert score>=minimum,(score,minimum)
artifact={'case':case,'library':'scikit-learn','version':version('scikit-learn'),'dataset':'Bundled digits: 1797 8×8 images',
          'split':'stratified 75/25, random_state=42','train_rows':len(y_train),'test_rows':len(y_test),
          'model':str(model),'accuracy':float(score),'expected_minimum':minimum,'device':'CPU; this example requests no GPU',
          'scope':'Small official-library example; not a complete reproduction of a paper or a general benchmark ranking'}
if case=='student-course':
    artifact['confusion_matrix']=confusion_matrix(y_test,predictions).tolist()
    artifact['first_predictions']=[{'expected':int(y_test[i]),'predicted':int(predictions[i])} for i in range(10)]
print(json.dumps(artifact,ensure_ascii=False,indent=2))
