# Python (Flask) HTTP Endpoint Example

By default is not using TLS. To test TLS capabilities change the following:

From
```python
app.run(host="127.0.0.1", port=5000, debug=True)
```
To
```python
app.run(host="127.0.0.1", port=5000, debug=True, ssl_context="adhoc")
```

For real world deployment please use proper certificates.