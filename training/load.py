from transformers import DistilBertTokenizerFast, DistilBertForQuestionAnswering, Trainer, TrainingArguments
from datasets import load_dataset
import time



def prepare_train_features(examples):
    # Tokenize our examples with truncation and padding
    # (so that they fit in the model)
    tokenized_examples = tokenizer(
        examples["question"],
        examples["context"],
        truncation="only_second",
        max_length=384,
        stride=128,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )
    
    # Since one example might give us several features if it is long,
    # we need a map from a feature to its corresponding example.
    sample_mapping = tokenized_examples.pop("overflow_to_sample_mapping")
    
    # The offset mappings will give us a map from token to character position
    offset_mapping = tokenized_examples.pop("offset_mapping")
    
    # Let's label those examples!
    tokenized_examples["start_positions"] = []
    tokenized_examples["end_positions"] = []
    
    for i, offsets in enumerate(offset_mapping):
        # We will label impossible answers with the index of the CLS token.
        input_ids = tokenized_examples["input_ids"][i]
        cls_index = input_ids.index(tokenizer.cls_token_id)
        
        # Grab the sequence corresponding to that example
        sequence_ids = tokenized_examples.sequence_ids(i)
        
        # One example can give several spans, this is the index of the example containing this span of text.
        sample_index = sample_mapping[i]
        answers = examples["answers"][sample_index]
        # If no answers are given, set the cls_index as answer.
        if len(answers["answer_start"]) == 0:
            tokenized_examples["start_positions"].append(cls_index)
            tokenized_examples["end_positions"].append(cls_index)
        else:
            # Start/end character index of the answer in the text
            start_char = answers["answer_start"][0]
            end_char = start_char + len(answers["text"][0])
            
            # Start token index of the current span in the text.
            token_start_index = 0
            while sequence_ids[token_start_index] != 1:
                token_start_index += 1
            
            # End token index of the current span in the text
            token_end_index = len(input_ids) - 1
            while sequence_ids[token_end_index] != 1:
                token_end_index -= 1
            
            # Detect if the answer is out of the span (in which case this feature is labeled with the CLS index).
            if not (offsets[token_start_index][0] <= start_char and offsets[token_end_index][1] >= end_char):
                tokenized_examples["start_positions"].append(cls_index)
                tokenized_examples["end_positions"].append(cls_index)
            else:
                # Otherwise move the token_start_index and token_end_index to the two ends of the answer.
                while token_start_index < len(offsets) and offsets[token_start_index][0] <= start_char:
                    token_start_index += 1
                tokenized_examples["start_positions"].append(token_start_index - 1)
                while offsets[token_end_index][1] >= end_char:
                    token_end_index -= 1
                tokenized_examples["end_positions"].append(token_end_index + 1)
    
    return tokenized_examples

def train_model():
    # Load the pre-trained DistilBERT tokenizer and model
    global tokenizer
    tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
    model = DistilBertForQuestionAnswering.from_pretrained("distilbert-base-uncased")

    # Define the training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=64,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir="./logs",
        logging_steps=10,
        eval_strategy="steps",
        evaluation_strategy="steps",
        eval_steps=100,
        save_steps=500,
        save_total_limit=2,
        max_steps=100  # REMOVE THIS
    )

    
    # Load the SQuAD dataset
    squad_dataset = load_dataset("squad")

    # Calculate total training steps
    batch_size = training_args.per_device_train_batch_size
    num_train_epochs = training_args.num_train_epochs
    num_examples = len(squad_dataset["train"])
    total_training_steps = (num_examples // batch_size) * num_train_epochs

    # Preprocess the dataset
    tokenized_squad = squad_dataset.map(prepare_train_features, batched=True, remove_columns=squad_dataset["train"].column_names)

    # Create a Trainer instance
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_squad["train"],
        eval_dataset=tokenized_squad["validation"]
    )

    # Train the model
    #trainer.train()

    start_time = time.time()
    trainer.train()
    end_time = time.time()

    time_per_100_steps = end_time - start_time
    estimated_total_time = (total_training_steps / 100) * time_per_100_steps

    print(f"Estimated total training time: {estimated_total_time / 3600:.2f} hours")


if __name__ == "__main__":
    train_model()
