import sys
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import GradientBoostingClassifier,RandomForestClassifier
from feature_engineering import refuting_features, polarity_features, hand_features, gen_or_load_feats
from feature_engineering import word_overlap_features, word_feature_features,head_feature_features
from utils.dataset import DataSet
from utils.generate_test_splits import kfold_split, get_stances_for_folds
from utils.score import report_score, LABELS, score_submission

from utils.system import parse_params, check_version



def generate_features(stances,dataset,name):
    h, b, y = [],[],[]

    for stance in stances:
        y.append(LABELS.index(stance['Stance']))
        h.append(stance['Headline'])
        b.append(dataset.articles[stance['Body ID']])

    X_overlap = gen_or_load_feats(word_overlap_features, h, b, "features/overlap."+name+".npy")
 
    X_refuting = gen_or_load_feats(refuting_features, h, b, "features/refuting."+name+".npy")
 
    X_polarity = gen_or_load_feats(polarity_features, h, b, "features/polarity."+name+".npy")
    X_hand = gen_or_load_feats(hand_features, h, b, "features/hand."+name+".npy")

    X_word = gen_or_load_feats(word_feature_features, h ,b, "features/word."+name+".npy")
    X_head = gen_or_load_feats(head_feature_features, h ,b, "features/head."+name+".npy")
    X = np.c_[X_hand, X_polarity, X_refuting, X_overlap,X_word,X_head]


    return X,y

if __name__ == "__main__":
    check_version()
    parse_params()

    d = DataSet()
    folds,hold_out = kfold_split(d,n_folds=10)
    fold_stances, hold_out_stances = get_stances_for_folds(d,folds,hold_out)
    

    Xs = dict()
    ys = dict()
   
    # Load/Precompute all features now
    X_holdout,y_holdout = generate_features(hold_out_stances,d,"holdout")
    for fold in fold_stances:
        Xs[fold],ys[fold] = generate_features(fold_stances[fold],d,str(fold))


    best_score = 0
    best_fold = None


    # Classifier for each fold
    for fold in fold_stances:
        ids = list(range(len(folds)))
        print("fold:"+ str(fold))
        print("ids:" + str(ids))
        del ids[fold]

        X_train = np.vstack(tuple([Xs[i] for i in ids]))
        y_train = np.hstack(tuple([ys[i] for i in ids]))

        X_test = Xs[fold]
        y_test = ys[fold]

        #clf = GradientBoostingClassifier(n_estimators=200, random_state=14128, verbose=True)
        clf = MLPClassifier()
        clf.fit(X_train, y_train)

        predicted = [LABELS[int(a)] for a in clf.predict(X_test)]
        actual = [LABELS[int(a)] for a in y_test]

        fold_score, _ = score_submission(actual, predicted)
        max_fold_score, _ = score_submission(actual, actual)

        score = fold_score/max_fold_score

        print("Score for fold "+ str(fold) + " was - " + str(score))
        if score > best_score:
            best_score = score
            best_fold = clf



    #Run on Holdout set and report the final score on the holdout set
    predicted = [LABELS[int(a)] for a in best_fold.predict(X_holdout)]
    actual = [LABELS[int(a)] for a in y_holdout]

    report_score(actual,predicted)
