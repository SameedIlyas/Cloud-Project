import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Flex, Box } from "@chakra-ui/react";
import { useEffect, useState } from "react";
import axios from "axios";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import { useAuthContext } from "./hooks/useAuthContext";
import Sidebar from "./components/Sidebar";

function App() {
  const { user, dispatch } = useAuthContext();
  const [usedStorage, setUsedStorage] = useState(0);
  const [loading, setLoading] = useState(true); // State to track loading state
  const [error, setError] = useState(null);

  // Verify Token when the app is initialized
  useEffect(() => {
    const verifyToken = async () => {
      const token =
        user?.access_token || localStorage.getItem("user")
          ? JSON.parse(localStorage.getItem("user")).access_token
          : null;

      if (token) {
        try {
          const response = await axios.get(
            "https://login-service-v2-935294039360.us-central1.run.app/verify/",
            {
              params: { token },
            }
          );

          if (response.status === 200) {
            setLoading(false); // Set loading to false after the token is verified
            console.log(response.data.message); // Token is valid
          }
        } catch (error) {
          console.error("Token is invalid, logging out...");
          setLoading(false);
          setError("Token is invalid, please log in again.");
          localStorage.removeItem("user");
          dispatch({ type: "LOGOUT" }); // Assuming your context has a logout action
        }
      } else {
        setLoading(false);
        dispatch({ type: "LOGOUT" });
      }
    };

    verifyToken();
  }, [user, dispatch]);

  if (loading) {
    return <div>Loading...</div>; // Show loading screen while token is being verified
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Flex>
          {user && <Sidebar usedStorage={usedStorage} />}
          <Box overflowY="auto" overflowX="hidden" h="100vh" w="100%" p="5">
            <Routes>
              <Route
                path="/login"
                element={user ? <Navigate to="/" /> : <Login />}
              />
              <Route
                path="/signup"
                element={user ? <Navigate to="/" /> : <Signup />}
              />
              <Route
                path="/"
                element={
                  user ? (
                    <Dashboard
                      setUsedStorage={setUsedStorage}
                      usedStorage={usedStorage}
                    />
                  ) : (
                    <Navigate to="/login" />
                  )
                }
              />
            </Routes>
          </Box>
        </Flex>
      </BrowserRouter>
    </div>
  );
}

export default App;
