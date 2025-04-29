TRANSACTION_INITIALIZE = """
subscription TransactionInitializeSession {
  event {
    ...TransactionInitializeSessionEvent
  }
}
fragment BasicWebhookMetadata on Event {
  issuedAt
  version
}
fragment PaymentGatewayRecipient on App {
  id
  privateMetadata {
    key
    value
  }
  metadata {
    key
    value
  }
}
fragment SyncWebhookTransaction on TransactionItem {
  id
  token
  pspReference
  events {
    pspReference
  }
}
fragment TransactionInitializeSessionEvent on TransactionInitializeSession {
  ...BasicWebhookMetadata
  __typename
  recipient {
    ...PaymentGatewayRecipient
  }
  idempotencyKey
  data
  merchantReference
  action {
    amount
    currency
    actionType
  }
  issuingPrincipal {
    ... on Node {
      id
    }
  }
  transaction {
    ...SyncWebhookTransaction
  }
}
"""
