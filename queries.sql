-- queries.sql : analysis on the cleaned bank.db (SQLite)
-- Tables: customers(customer_id, full_name, city, signup_date)
--         transactions(txn_id, customer_id, txn_date, amount, category, status)

-- 1) JOIN + GROUP BY: total completed spending per city
SELECT c.city,
       COUNT(*)               AS txn_count,
       ROUND(SUM(t.amount), 2) AS total_amount
FROM transactions t
JOIN customers c ON c.customer_id = t.customer_id
WHERE t.status = 'completed'
GROUP BY c.city
ORDER BY total_amount DESC;

-- 2) HAVING: customers with more than 8 transactions
SELECT c.full_name,
       COUNT(*) AS txn_count
FROM customers c
JOIN transactions t ON t.customer_id = c.customer_id
GROUP BY c.customer_id, c.full_name
HAVING COUNT(*) > 8
ORDER BY txn_count DESC;

-- 3) CTE + subquery: customers whose total spending is above the average customer
WITH customer_totals AS (
    SELECT customer_id,
           SUM(amount) AS total_amount
    FROM transactions
    WHERE status = 'completed'
    GROUP BY customer_id
)
SELECT c.full_name,
       ROUND(ct.total_amount, 2) AS total_amount
FROM customer_totals ct
JOIN customers c ON c.customer_id = ct.customer_id
WHERE ct.total_amount > (SELECT AVG(total_amount) FROM customer_totals)
ORDER BY ct.total_amount DESC;

-- 4) Window function: running total of spending per customer over time
SELECT customer_id,
       txn_date,
       amount,
       ROUND(SUM(amount) OVER (
           PARTITION BY customer_id
           ORDER BY txn_date, txn_id
       ), 2) AS running_total
FROM transactions
WHERE status = 'completed'
ORDER BY customer_id, txn_date
LIMIT 30;

-- 5) Window function (ROW_NUMBER) + CTE: top 3 biggest transactions per customer
WITH ranked AS (
    SELECT customer_id,
           txn_id,
           amount,
           ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY amount DESC) AS rn
    FROM transactions
)
SELECT customer_id, txn_id, amount
FROM ranked
WHERE rn <= 3
ORDER BY customer_id, rn;

-- 6) Monthly trend: total amount per month
SELECT strftime('%Y-%m', txn_date) AS month,
       ROUND(SUM(amount), 2)       AS total_amount
FROM transactions
WHERE status = 'completed'
GROUP BY month
ORDER BY month;
