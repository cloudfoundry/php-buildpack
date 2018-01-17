if [[ -z "${NEWRELIC_LICENSE:-}" ]]; then
  export NEWRELIC_LICENSE=$(echo $VCAP_SERVICES  | jq -r '.newrelic[0].credentials.licenseKey')
fi
