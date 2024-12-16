from transformers import pipeline

class MHModel:

    @staticmethod
    def predict(text):
        classifier = pipeline('text-classification', model='./fine_tuned_model')
        prediction = classifier(text)
        label = prediction[0]['label']
        if label == "LABEL_1":
            label = "1"
        else:
            label = "0"
        score = prediction[0]['score']
        print(f"Label: {label}, Score: {score}")
        return label, score
    
# Test run
# MHModel.predict("I am so depressed")