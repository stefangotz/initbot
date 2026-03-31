# Google Cloud Services

Notes on running an instance of the project in Google Cloud Services

## CLI Setup

#### Installation

    brew install --cask google-cloud-sdk

or

    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL

#### Authentication

    gcloud auth login

#### Set default project

    gcloud projects list
    gcloud config set project YOUR_PROJECT_ID

#### Verification

    gcloud compute instances list

## Google Compute Engine

#### SSH Access

    gcloud compute ssh YOUR_INSTANCE_NAME --zone YOUR_ZONE

#### Instance Configuration for Web App

Check existing firewall rules

    gcloud compute firewall-rules list

If there are no rules for HTTP or HTTPS, add them with

    gcloud compute firewall-rules create allow-http     --allow tcp:80     --target-tags http-server     --description "Allow HTTP for Caddy ACME challenge"

    gcloud compute firewall-rules create allow-https     --allow tcp:443,udp:443     --target-tags https-server     --description "Allow HTTPS and HTTP/3"

    gcloud compute instances add-tags YOUR_INSTANCE_NAME     --tags http-server,https-server     --zone YOUR_ZONE
