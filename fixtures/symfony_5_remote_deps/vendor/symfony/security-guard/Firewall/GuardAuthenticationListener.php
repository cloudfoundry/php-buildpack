<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Guard\Firewall;

use Psr\Log\LoggerInterface;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\Security\Core\Authentication\AuthenticationManagerInterface;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;
use Symfony\Component\Security\Guard\AuthenticatorInterface;
use Symfony\Component\Security\Guard\GuardAuthenticatorHandler;
use Symfony\Component\Security\Guard\Token\PreAuthenticationGuardToken;
use Symfony\Component\Security\Http\Firewall\AbstractListener;
use Symfony\Component\Security\Http\RememberMe\RememberMeServicesInterface;

/**
 * Authentication listener for the "guard" system.
 *
 * @author Ryan Weaver <ryan@knpuniversity.com>
 * @author Amaury Leroux de Lens <amaury@lerouxdelens.com>
 *
 * @final
 */
class GuardAuthenticationListener extends AbstractListener
{
    private $guardHandler;
    private $authenticationManager;
    private $providerKey;
    private $guardAuthenticators;
    private $logger;
    private $rememberMeServices;

    /**
     * @param string                            $providerKey         The provider (i.e. firewall) key
     * @param iterable|AuthenticatorInterface[] $guardAuthenticators The authenticators, with keys that match what's passed to GuardAuthenticationProvider
     */
    public function __construct(GuardAuthenticatorHandler $guardHandler, AuthenticationManagerInterface $authenticationManager, string $providerKey, iterable $guardAuthenticators, LoggerInterface $logger = null)
    {
        if (empty($providerKey)) {
            throw new \InvalidArgumentException('$providerKey must not be empty.');
        }

        $this->guardHandler = $guardHandler;
        $this->authenticationManager = $authenticationManager;
        $this->providerKey = $providerKey;
        $this->guardAuthenticators = $guardAuthenticators;
        $this->logger = $logger;
    }

    /**
     * {@inheritdoc}
     */
    public function supports(Request $request): ?bool
    {
        if (null !== $this->logger) {
            $context = ['firewall_key' => $this->providerKey];

            if ($this->guardAuthenticators instanceof \Countable || \is_array($this->guardAuthenticators)) {
                $context['authenticators'] = \count($this->guardAuthenticators);
            }

            $this->logger->debug('Checking for guard authentication credentials.', $context);
        }

        $guardAuthenticators = [];

        foreach ($this->guardAuthenticators as $key => $guardAuthenticator) {
            if (null !== $this->logger) {
                $this->logger->debug('Checking support on guard authenticator.', ['firewall_key' => $this->providerKey, 'authenticator' => \get_class($guardAuthenticator)]);
            }

            if ($guardAuthenticator->supports($request)) {
                $guardAuthenticators[$key] = $guardAuthenticator;
            } elseif (null !== $this->logger) {
                $this->logger->debug('Guard authenticator does not support the request.', ['firewall_key' => $this->providerKey, 'authenticator' => \get_class($guardAuthenticator)]);
            }
        }

        if (!$guardAuthenticators) {
            return false;
        }

        $request->attributes->set('_guard_authenticators', $guardAuthenticators);

        return true;
    }

    /**
     * Iterates over each authenticator to see if each wants to authenticate the request.
     */
    public function authenticate(RequestEvent $event)
    {
        $request = $event->getRequest();
        $guardAuthenticators = $request->attributes->get('_guard_authenticators');
        $request->attributes->remove('_guard_authenticators');

        foreach ($guardAuthenticators as $key => $guardAuthenticator) {
            // get a key that's unique to *this* guard authenticator
            // this MUST be the same as GuardAuthenticationProvider
            $uniqueGuardKey = $this->providerKey.'_'.$key;

            $this->executeGuardAuthenticator($uniqueGuardKey, $guardAuthenticator, $event);

            if ($event->hasResponse()) {
                if (null !== $this->logger) {
                    $this->logger->debug('The "{authenticator}" authenticator set the response. Any later authenticator will not be called', ['authenticator' => \get_class($guardAuthenticator)]);
                }

                break;
            }
        }
    }

    private function executeGuardAuthenticator(string $uniqueGuardKey, AuthenticatorInterface $guardAuthenticator, RequestEvent $event)
    {
        $request = $event->getRequest();
        try {
            if (null !== $this->logger) {
                $this->logger->debug('Calling getCredentials() on guard authenticator.', ['firewall_key' => $this->providerKey, 'authenticator' => \get_class($guardAuthenticator)]);
            }

            // allow the authenticator to fetch authentication info from the request
            $credentials = $guardAuthenticator->getCredentials($request);

            if (null === $credentials) {
                throw new \UnexpectedValueException(sprintf('The return value of "%1$s::getCredentials()" must not be null. Return false from "%1$s::supports()" instead.', get_debug_type($guardAuthenticator)));
            }

            // create a token with the unique key, so that the provider knows which authenticator to use
            $token = new PreAuthenticationGuardToken($credentials, $uniqueGuardKey);

            if (null !== $this->logger) {
                $this->logger->debug('Passing guard token information to the GuardAuthenticationProvider', ['firewall_key' => $this->providerKey, 'authenticator' => \get_class($guardAuthenticator)]);
            }
            // pass the token into the AuthenticationManager system
            // this indirectly calls GuardAuthenticationProvider::authenticate()
            $token = $this->authenticationManager->authenticate($token);

            if (null !== $this->logger) {
                $this->logger->info('Guard authentication successful!', ['token' => $token, 'authenticator' => \get_class($guardAuthenticator)]);
            }

            // sets the token on the token storage, etc
            $this->guardHandler->authenticateWithToken($token, $request, $this->providerKey);
        } catch (AuthenticationException $e) {
            // oh no! Authentication failed!

            if (null !== $this->logger) {
                $this->logger->info('Guard authentication failed.', ['exception' => $e, 'authenticator' => \get_class($guardAuthenticator)]);
            }

            $response = $this->guardHandler->handleAuthenticationFailure($e, $request, $guardAuthenticator, $this->providerKey);

            if ($response instanceof Response) {
                $event->setResponse($response);
            }

            return;
        }

        // success!
        $response = $this->guardHandler->handleAuthenticationSuccess($token, $request, $guardAuthenticator, $this->providerKey);
        if ($response instanceof Response) {
            if (null !== $this->logger) {
                $this->logger->debug('Guard authenticator set success response.', ['response' => $response, 'authenticator' => \get_class($guardAuthenticator)]);
            }

            $event->setResponse($response);
        } else {
            if (null !== $this->logger) {
                $this->logger->debug('Guard authenticator set no success response: request continues.', ['authenticator' => \get_class($guardAuthenticator)]);
            }
        }

        // attempt to trigger the remember me functionality
        $this->triggerRememberMe($guardAuthenticator, $request, $token, $response);
    }

    /**
     * Should be called if this listener will support remember me.
     */
    public function setRememberMeServices(RememberMeServicesInterface $rememberMeServices)
    {
        $this->rememberMeServices = $rememberMeServices;
    }

    /**
     * Checks to see if remember me is supported in the authenticator and
     * on the firewall. If it is, the RememberMeServicesInterface is notified.
     */
    private function triggerRememberMe(AuthenticatorInterface $guardAuthenticator, Request $request, TokenInterface $token, Response $response = null)
    {
        if (null === $this->rememberMeServices) {
            if (null !== $this->logger) {
                $this->logger->debug('Remember me skipped: it is not configured for the firewall.', ['authenticator' => \get_class($guardAuthenticator)]);
            }

            return;
        }

        if (!$guardAuthenticator->supportsRememberMe()) {
            if (null !== $this->logger) {
                $this->logger->debug('Remember me skipped: your authenticator does not support it.', ['authenticator' => \get_class($guardAuthenticator)]);
            }

            return;
        }

        if (!$response instanceof Response) {
            throw new \LogicException(sprintf('"%s::onAuthenticationSuccess()" *must* return a Response if you want to use the remember me functionality. Return a Response, or set remember_me to false under the guard configuration.', get_debug_type($guardAuthenticator)));
        }

        $this->rememberMeServices->loginSuccess($request, $response, $token);
    }
}
