# Image Transmission

## Run the pipeline

Start the receiver on the Rebel server:

```bash
python rebel_sever.py
```

On the image system, create the bundle:

```bash
python ImageSorter.py --top 10
```

The default output is `Target.zip`. Its contents are XOR-encrypted by
`ImageSorter.py`; it will not open as a ZIP until the Rebel server decrypts it.
Send it as before:

```bash
python send_image.py --file ./Target.zip --server REBEL_SERVER_IP
```

After a complete transfer, the Rebel server decrypts the bundle and saves a
normal, viewable ZIP in `received/Target.zip`. Unzip that file to view the
selected images.

The sender and receiver contain matching values for `ENCRYPTION_KEY` and
`ENCRYPTED_HEADER`. If you change the key in `ImageSorter.py`, change it in
`rebel_sever.py` too.

## Note about this encryption

This uses repeating-key XOR from Python's standard library, so there are no
additional packages to install. It is a simple reversible project-level
encryption layer and is not suitable for protecting sensitive information
against a capable attacker.

## Expected receiver output

```text
rebel server listening on port 5000...
connection from ('192.168.x.x', ...)
receiving Target.zip (123456 bytes)...
received 123456/123456 bytes
decrypted bundle saved to .../received/Target.zip
```

## TODO

- Change the normal TCP portion to use radio.
