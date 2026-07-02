# AI Diagnosis Report

## Summary

The insufficient stock order scenario returned HTTP 500 instead of the expected HTTP 409.

## Suspected root cause

The order API is likely allowing a domain exception to escape without mapping it to a business error response.

## Reproduction steps

1. Log in as `alice`.
2. Send `POST /api/orders` with `product_id=1` and `quantity=99`.
3. Observe that the response status is 500.

## Evidence

The failing test expected status code 409 but received 500.

## Suggested fix

Catch the stock validation exception in the order endpoint and return HTTP 409 with a clear error message.

## Risk level

Medium

## Classification

product bug
