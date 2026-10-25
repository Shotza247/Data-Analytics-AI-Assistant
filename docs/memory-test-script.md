# Memory test script (sample_data.csv)

Purpose: check, with the real OpenAI model, that the short-term and long-term memory
keep follow-ups working after the earliest turns have left the 8-message window.

Setup
1. Make sure `.streamlit/secrets.toml` has a real `OpenAI_API_Key`.
2. `streamlit run app.py`, upload `sample_data.csv`.
3. Industry: Retail / E-commerce. Goal: "Help the sales manager decide where to focus."
4. Ask the questions below one at a time, in order. The session limit is 10 requests,
   so this script uses 9 questions and leaves one spare. Each question can trigger
   two API calls, but only user requests count toward the limit.

Questions
 1. Which product category brings in the most revenue?
 2. Show the monthly revenue trend as a chart.
 3. Which customer region has the highest average order value?
 4. Which payment method is used most, and does it differ by region?
 5. What are the top 5 products by total amount?
 6. (memory check) Going back to my first question: which category was it, and how much of total revenue did it bring in?
 7. (memory check) What was the chart in my second question about, and what was the main caveat?
 8. Break the top revenue category down by region.
 9. (memory check) Remind me which region had the highest average order value earlier.

What to look for
- Question 6: only turn 1 (question 1 and its answer) is a memory note by now. The model should
  name the category and give a revenue share, or say it will recompute from the data. It should not invent a number.
- Question 7: turns 1 and 2 are memory notes. The note for turn 2 keeps the chart title and one
  caveat. If the answer is vague, the note was too thin.
- Question 9: turns 1 to 4 are memory notes, so turn 3 (the average order value by region)
  is only available as a note. This tests whether a note is enough.
- Check the sidebar: input tokens per request should grow slowly after turn 5 rather than
  climbing every turn. If your provider reports cached tokens, a cached line appears.
- Wrong answers: compare with sample_data.csv. Known values: Fitness has 28 of 60 orders;
  the strongest correlation is Unit Price vs Total Amount (0.77).

Record the results
 Q   Right / partly / wrong   Notes (did it use memory, recompute, or guess?)
 6
 7
 9

If 2 or more of the 3 memory checks are wrong, the notes are too thin. Tell me which ones
and I will adjust what the note keeps.
